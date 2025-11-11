package com.example.datasets.service;

import com.example.datasets.dao.HwDataset;
import com.example.datasets.dao.HwDatasetRepository;
import jakarta.transaction.Transactional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class HwDatasetServiceImpl implements HwDatasetService {

    @Autowired
    private HwDatasetRepository hwDatasetRepository;

    @Override
    public List<HwDataset> getAllDatasets() {
        return hwDatasetRepository.findAll();
    }

    @Override
    public HwDataset uploadDataset(HwDataset dataset) {
        // 检查数据集名称是否已存在
        if (hwDatasetRepository.existsByName(dataset.getName())) {
            throw new RuntimeException("数据集名称已存在: " + dataset.getName());
        }
        return hwDatasetRepository.save(dataset);
    }

    @Override
    @Transactional
    public void deleteDatasetByName(String name) {
        // 检查数据集是否存在
        HwDataset dataset = hwDatasetRepository.findByName(name);
        if (dataset == null) {
            throw new RuntimeException("数据集不存在: " + name);
        }
        hwDatasetRepository.deleteByName(name);

        // 删除本地文件
        try {
            java.nio.file.Path filePath = java.nio.file.Paths.get(dataset.getAddress());
            java.nio.file.Files.deleteIfExists(filePath);
        } catch (Exception e) {
            // 捕获异常，但不回滚数据库事务
            System.err.println("文件删除失败: " + e.getMessage());
        }
    }
}
