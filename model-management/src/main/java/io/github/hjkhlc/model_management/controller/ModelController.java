package io.github.hjkhlc.model_management.controller;

import io.github.hjkhlc.model_management.entity.ModelEntity;
import io.github.hjkhlc.model_management.service.ModelService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/models")
@RequiredArgsConstructor
@PreAuthorize("hasRole('ADMIN')") // 假设Spring Security配置，管理员角色访问
public class ModelController {

    private final ModelService modelService;

    /**
     * 接口1: 获取所有模型列表
     * @return 模型列表
     */
    @GetMapping
    public ResponseEntity<List<ModelEntity>> getAllModels() {
        try {
            List<ModelEntity> models = modelService.getAllModels();
            log.info("Retrieved {} models", models.size());
            return ResponseEntity.ok(models);
        } catch (Exception e) {
            log.error("Error retrieving models: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * 接口2: 切换当前模型
     * @param requestBody 包含modelName的JSON
     * @return 切换消息
     */
    @PostMapping("/apply")
    public ResponseEntity<Map<String, String>> switchActiveModel(@RequestBody Map<String, String> requestBody) {
        String modelName = requestBody.get("modelName");
        if (modelName == null || modelName.trim().isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "modelName is required"));
        }
        try {
            modelService.switchActiveModel(modelName);
            log.info("Switched active model to: {}", modelName);
            return ResponseEntity.ok(Map.of("msg", "模型已切换"));
        } catch (IllegalArgumentException e) {
            log.warn("Switch failed: {}", e.getMessage());
            return ResponseEntity.badRequest()
                    .body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            log.error("Error switching model: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * 接口3: 删除模型
     * @param modelName 模型名称（路径变量）
     * @return 删除消息
     */
    @DeleteMapping("/{modelName}")
    public ResponseEntity<Map<String, String>> deleteModel(@PathVariable String modelName) {
        if (modelName == null || modelName.trim().isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "modelName is required"));
        }
        try {
            modelService.deleteModel(modelName);
            log.info("Deleted model: {}", modelName);
            return ResponseEntity.ok(Map.of("msg", "模型删除成功"));
        } catch (IllegalArgumentException e) {
            log.warn("Delete failed: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            log.error("Error deleting model: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}