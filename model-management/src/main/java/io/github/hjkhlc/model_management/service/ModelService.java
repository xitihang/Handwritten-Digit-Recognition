package io.github.hjkhlc.model_management.service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Stream;

import org.apache.commons.io.FileUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.databind.ObjectMapper;

import io.github.hjkhlc.model_management.entity.ModelEntity;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class ModelService {

    @Value("${app.models.dir:/models}") // application.yml中配置：app.models.dir: /path/to/models
    private String modelsDirPath;

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final DateTimeFormatter dateFormatter = DateTimeFormatter.ISO_LOCAL_DATE_TIME;

    /**
     * 空函数：通知Python端切换模型（占位，后续用RestTemplate实现）
     * @param modelName 模型名称
     */
    private void notifyPythonSwitch(String modelName) {
        // TODO: 实际实现：RestTemplate postToPython("/api/switch_model", Map.of("model", modelName));
        log.info("Notifying Python server to switch to model: {}", modelName);
        // 模拟延迟：Thread.sleep(1000); // 假设Python端响应<1s
    }

    /**
     * 获取所有模型列表
     * @return 排序后的模型列表
     */
    public List<ModelEntity> getAllModels() {
        Path modelsDir = Paths.get(modelsDirPath);
        ensureDirectoryExists(modelsDir);

        String activeModelName = getActiveModelName();
        List<ModelEntity> models = new ArrayList<>();

        try (Stream<Path> paths = Files.walk(modelsDir, 1)) {
            paths.filter(Files::isDirectory)
                    .filter(path -> !path.equals(modelsDir)) // 排除根目录
                    .forEach(modelDir -> {
                        ModelEntity entity = loadModelFromDir(modelDir, activeModelName);
                        if (entity != null) {
                            models.add(entity);
                        }
                    });
        } catch (IOException e) {
            log.error("Error walking models directory: {}", e.getMessage());
            throw new RuntimeException("Failed to scan models", e);
        }

        // 按trainDate降序排序
        models.sort((m1, m2) -> m2.getTrainDate().compareTo(m1.getTrainDate()));
        return models;
    }

    /**
     * 从目录加载模型实体
     * @param modelDir 模型目录
     * @param activeModelName 活跃模型名称
     * @return ModelEntity 或 null（如果加载失败）
     */
    private ModelEntity loadModelFromDir(Path modelDir, String activeModelName) {
        Path metadataPath = modelDir.resolve("metadata.json");
        if (!Files.exists(metadataPath)) {
            log.warn("Metadata missing for model dir: {}", modelDir);
            return null;
        }

        try {
            String jsonContent = Files.readString(metadataPath);
            ModelEntity entity = objectMapper.readValue(jsonContent, ModelEntity.class);

            // 如果metadata.json中无id，生成一个
            if (entity.getId() == null || entity.getId().isEmpty()) {
                entity.setId(UUID.randomUUID().toString());
                saveMetadata(modelDir, entity); // 原子更新
            }

            // 设置活跃状态
            entity.setActive(activeModelName != null && activeModelName.equals(entity.getName()));

            // 示例填充：如果trainDate为空，使用当前日期（实际应从训练时设置）
            if (entity.getTrainDate() == null) {
                entity.setTrainDate(LocalDateTime.now());
                saveMetadata(modelDir, entity);
            }

            return entity;
        } catch (IOException e) {
            log.warn("Failed to load metadata for {}: {}", modelDir, e.getMessage());
            return null;
        }
    }

    /**
     * 切换活跃模型
     * @param modelName 模型名称
     */
    public void switchActiveModel(String modelName) {
        List<ModelEntity> models = getAllModels();
        Optional<ModelEntity> targetModel = models.stream()
                .filter(m -> m.getName().equals(modelName))
                .findFirst();

        if (targetModel.isEmpty()) {
            throw new IllegalArgumentException("模型不存在");
        }

        Path activePath = Paths.get(modelsDirPath, "active.json");
        Map<String, String> activeMap = Map.of("activeModel", modelName);
        try {
            objectMapper.writeValue(activePath.toFile(), activeMap);
            notifyPythonSwitch(modelName);
        } catch (IOException e) {
            log.error("Failed to update active model: {}", e.getMessage());
            throw new RuntimeException("切换失败", e);
        }
    }

    /**
     * 删除模型
     * @param modelName 模型名称
     */
    public void deleteModel(String modelName) {
        String activeModelName = getActiveModelName();
        if (activeModelName != null && activeModelName.equals(modelName)) {
            throw new IllegalArgumentException("活跃模型不可删除，请先切换");
        }

        Path modelPath = Paths.get(modelsDirPath, modelName);
        if (!Files.exists(modelPath)) {
            throw new IllegalArgumentException("模型不存在");
        }

        try {
            FileUtils.deleteDirectory(modelPath.toFile()); // 递归删除
            log.info("Deleted model directory: {}", modelPath);
        } catch (IOException e) {
            log.error("Failed to delete model: {}", e.getMessage());
            throw new RuntimeException("删除失败", e);
        }
    }

    /**
     * 获取活跃模型名称
     * @return activeModel 或 null
     */
    private String getActiveModelName() {
        Path activePath = Paths.get(modelsDirPath, "active.json");
        if (!Files.exists(activePath)) {
            return null;
        }
        try {
            @SuppressWarnings("unchecked")
            Map<String, String> activeMap = objectMapper.readValue(activePath.toFile(), Map.class);
            return activeMap.get("activeModel");
        } catch (IOException e) {
            log.warn("Failed to read active model: {}", e.getMessage());
            return null;
        }
    }

    /**
     * 确保目录存在
     * @param dir 目录路径
     */
    private void ensureDirectoryExists(Path dir) {
        try {
            Files.createDirectories(dir);
        } catch (IOException e) {
            log.error("Failed to create models directory: {}", e.getMessage());
            throw new RuntimeException("初始化目录失败", e);
        }
    }

    /**
     * 保存模型元数据（原子更新）
     * @param modelDir 模型目录
     * @param entity 实体
     */
    private void saveMetadata(Path modelDir, ModelEntity entity) {
        Path metadataPath = modelDir.resolve("metadata.json");
        try {
            entity.setTrainDate(entity.getTrainDate() != null ? entity.getTrainDate() : LocalDateTime.now());
            String json = objectMapper.writeValueAsString(entity);
            Files.writeString(metadataPath, json, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
        } catch (IOException e) {
            log.error("Failed to save metadata for {}: {}", modelDir, e.getMessage());
        }
    }
}