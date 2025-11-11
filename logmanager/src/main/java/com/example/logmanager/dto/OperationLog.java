package com.example.logmanager.dto;

public class OperationLog {
    private String user;
    private String action;
    private String time;

    public OperationLog() {
    }

    public OperationLog(String user, String action, String time) {
        this.user = user;
        this.action = action;
        this.time = time;
    }

    public String getUser() {
        return user;
    }

    public void setUser(String user) {
        this.user = user;
    }

    public String getAction() {
        return action;
    }

    public void setAction(String action) {
        this.action = action;
    }

    public String getTime() {
        return time;
    }

    public void setTime(String time) {
        this.time = time;
    }
}


