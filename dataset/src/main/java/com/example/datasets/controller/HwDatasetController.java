package com.example.datasets.controller;

import com.example.datasets.dao.HwDataset;
import com.example.datasets.service.HwDatasetService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/datasets")
public class HwDatasetController {
    @Autowired
    private HwDatasetService hwDatasetService;

    // 1. GET /api/datasets - 返回所有数据集的信息[{name, numImages}]
    @GetMapping
    public List<Map<String, Object>> getAllDatasets() {
        List<HwDataset> datasets = hwDatasetService.getAllDatasets();

        return datasets.stream().map(dataset -> {
            Map<String, Object> datasetInfo = new HashMap<>();
            datasetInfo.put("name", dataset.getName());
            datasetInfo.put("numImages", dataset.getNumImages());
            return datasetInfo;
        }).collect(Collectors.toList());
    }


    // 2. POST /api/datasets/upload - 请求体FormData（文件+meta）- 返回{"msg": "上传是否成功"}
    @PostMapping("/upload")
    public Map<String, String> uploadDataset(
            @RequestParam("file") MultipartFile file,
            @RequestParam("name") String name,
            @RequestParam("numImages") String numImages) {  // 移除了address参数

        Long count = Long.parseLong(numImages);
        Map<String, String> response = new HashMap<>();

        try {
            // 检查文件是否为空
            if (file.isEmpty()) {
                response.put("msg", "上传失败: 文件不能为空");
                return response;
            }

            // 定义保存目录
            String baseDir = "D:\\university\\spring_boot_proj\\dataset_save";
            String filePath = baseDir + "\\" + file.getOriginalFilename();

            // 创建目录（如果不存在）
            java.nio.file.Path dirPath = java.nio.file.Paths.get(baseDir);
            if (!java.nio.file.Files.exists(dirPath)) {
                java.nio.file.Files.createDirectories(dirPath);
            }

            // 保存文件
            java.nio.file.Path targetPath = java.nio.file.Paths.get(filePath);
            file.transferTo(targetPath.toFile());

            // 创建数据集对象，address为完整文件路径
            HwDataset dataset = new HwDataset();
            dataset.setName(name);
            dataset.setNumImages(count);
            dataset.setAddress(filePath);  // 使用完整文件路径作为address

            // 调用Service上传
            hwDatasetService.uploadDataset(dataset);

            response.put("msg", "上传成功");
        } catch (Exception e) {
            response.put("msg", "上传失败: " + e.getMessage());
            e.printStackTrace();  // 打印错误日志
        }

        return response;
    }

    // 3. DELETE /api/datasets/{datasetName} - 返回{"msg": "删除是否成功"}
    @DeleteMapping("/{datasetName}")
    public Map<String, String> deleteDataset(@PathVariable String datasetName) {
        Map<String, String> response = new HashMap<>();

        try {
            hwDatasetService.deleteDatasetByName(datasetName);
            response.put("msg", "删除成功");
        } catch (Exception e) {
            response.put("msg", "删除失败: " + e.getMessage());
        }

        return response;
    }
}
