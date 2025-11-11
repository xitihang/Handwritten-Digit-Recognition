package com.example.datasets.service;

import com.example.datasets.dao.HwDataset;

import java.util.List;

public interface HwDatasetService {
    // 1. 返回所有数据集的信息
    List<HwDataset> getAllDatasets();

    // 2. 上传新的数据集
    HwDataset uploadDataset(HwDataset dataset);

    // 3. 删除数据集（用name）
    void deleteDatasetByName(String name);
}
