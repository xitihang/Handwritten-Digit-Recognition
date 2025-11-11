package com.example.datasets.dao;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface HwDatasetRepository extends JpaRepository<HwDataset, String> {
    // 根据名称精确查找
    HwDataset findByName(String name);

    // 检查是否存在
    boolean existsByName(String name);

    // 根据名称删除
    void deleteByName(String name);
}
