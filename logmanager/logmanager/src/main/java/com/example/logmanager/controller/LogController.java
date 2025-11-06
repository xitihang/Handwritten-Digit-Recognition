package com.example.logmanager.controller;

import com.example.logmanager.dto.OperationLog;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;

import jakarta.annotation.PostConstruct;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

@RestController
@RequestMapping(path = "/api/logs", produces = MediaType.APPLICATION_JSON_VALUE)
public class LogController {

    private final CopyOnWriteArrayList<OperationLog> logs = new CopyOnWriteArrayList<>();

    @PostConstruct
    public void init() {
        logs.add(new OperationLog("admin", "登录系统", "2025-10-22 09:25:30"));
        logs.add(new OperationLog("researcher01", "上传新数据集 (MNIST-扩展v2)", "2025-10-22 10:15:42"));
        logs.add(new OperationLog("admin", "启动训练任务", "2025-10-22 10:32:18"));
    }

    @GetMapping
    public List<OperationLog> list() {
        return logs;
    }

    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE)
    public OperationLog add(@RequestBody OperationLog log) {
        logs.add(log);
        return log;
    }
}


