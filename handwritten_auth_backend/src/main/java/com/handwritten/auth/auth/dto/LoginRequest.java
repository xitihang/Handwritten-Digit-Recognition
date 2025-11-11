package com.handwritten.auth.auth.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public class LoginRequest {
    @NotNull
    private Long userid;
    @NotBlank
    private String password;
    @NotBlank
    private String verifyCode;
    @NotBlank
    private String verifyCodeId;

    private ClientInfo clientInfo;

    public static class ClientInfo {
        private String os;
        private String browser;
        private String loginIp;

        public String getOs() { return os; }
        public void setOs(String os) { this.os = os; }
        public String getBrowser() { return browser; }
        public void setBrowser(String browser) { this.browser = browser; }
        public String getLoginIp() { return loginIp; }
        public void setLoginIp(String loginIp) { this.loginIp = loginIp; }
    }

    public Long getUserid() { return userid; }
    public void setUserid(Long userid) { this.userid = userid; }
    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }
    public String getVerifyCode() { return verifyCode; }
    public void setVerifyCode(String verifyCode) { this.verifyCode = verifyCode; }
    public String getVerifyCodeId() { return verifyCodeId; }
    public void setVerifyCodeId(String verifyCodeId) { this.verifyCodeId = verifyCodeId; }
    public ClientInfo getClientInfo() { return clientInfo; }
    public void setClientInfo(ClientInfo clientInfo) { this.clientInfo = clientInfo; }
}


