package com.example.logmanager.controller;

import com.example.logmanager.dto.OperationLog;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

@RestController
@RequestMapping(path = "/api/logs", produces = MediaType.APPLICATION_JSON_VALUE)
public class LogController {

    private final CopyOnWriteArrayList<OperationLog> logs = new CopyOnWriteArrayList<>();

    // 移除硬编码的初始数据，只记录实时活动

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


