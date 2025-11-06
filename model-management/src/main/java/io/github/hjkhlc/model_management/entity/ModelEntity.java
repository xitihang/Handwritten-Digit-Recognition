package io.github.hjkhlc.model_management.entity;

import java.time.LocalDateTime;
import java.util.UUID;

import lombok.Data;

@Data
public class ModelEntity {
    private String id = UUID.randomUUID().toString(); // 生成唯一ID
    private String name;
    private String user;
    private String trainTime; // ISO-8601格式，如 "PT2H30M"
    private double accuracy;
    private String version;
    private LocalDateTime trainDate;
    private boolean active = false;
}