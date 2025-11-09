package com.handwritten.auth.auth;

import com.handwritten.auth.captcha.CaptchaService;
import com.handwritten.auth.captcha.CaptchaService.CaptchaResult;
import com.handwritten.auth.common.ApiResponse;
import com.handwritten.auth.common.BusinessException;
import com.handwritten.auth.common.UnauthorizedException;
import com.handwritten.auth.auth.dto.LoginRequest;
import com.handwritten.auth.user.entity.AuthUser;
import com.handwritten.auth.user.repo.AuthUserRepository;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final CaptchaService captchaService;
    private final AuthUserRepository userRepository;

    @Value("${app.security.admin-only-id:1}")
    private Long adminOnlyId;

    public AuthController(CaptchaService captchaService, AuthUserRepository userRepository) {
        this.captchaService = captchaService;
        this.userRepository = userRepository;
    }

    @GetMapping("/getVerifyCodeImg")
    public ApiResponse<Map<String, Object>> getVerifyCodeImg() {
        CaptchaResult r = captchaService.generateCaptcha();
        Map<String, Object> data = new HashMap<>();
        data.put("verifyCodeId", r.verifyCodeId);
        data.put("verifyCodeImgBase64", r.verifyCodeImgBase64);
        data.put("expireTime", r.expireTime.toString());
        return ApiResponse.success("验证码图片获取成功", data);
    }

    @PostMapping("/login")
    public ApiResponse<Map<String, Object>> login(@Valid @RequestBody LoginRequest req, HttpServletRequest httpReq) {
        boolean ok = captchaService.validate(req.getVerifyCodeId(), req.getVerifyCode());
        if (!ok) {
            throw new BusinessException(400, "验证码错误或已过期");
        }

        Optional<AuthUser> opt = userRepository.findById(req.getUserid());
        if (opt.isEmpty()) {
            throw new BusinessException(400, "账号或密码错误");
        }
        AuthUser user = opt.get();

        if (!user.getPassword().equals(req.getPassword())) {
            throw new BusinessException(400, "账号或密码错误");
        }

        if (!req.getUserid().equals(adminOnlyId)) {
            throw new BusinessException(400, "无权登录");
        }

        String ip = req.getClientInfo() != null && req.getClientInfo().getLoginIp() != null
                ? req.getClientInfo().getLoginIp()
                : httpReq.getRemoteAddr();
        user.setLastLoginTime(LocalDateTime.now());
        user.setLastLoginIp(ip);
        userRepository.save(user);

        HttpSession session = httpReq.getSession(true);
        session.setAttribute("currentUserId", user.getId());

        Map<String, Object> data = new HashMap<>();
        Map<String, Object> userInfo = new HashMap<>();
        userInfo.put("id", user.getId());
        data.put("user", userInfo);
        return ApiResponse.success("登录成功", data);
    }

    @GetMapping("/currentUser")
    public ApiResponse<Map<String, Object>> currentUser(HttpServletRequest httpReq) {
        HttpSession session = httpReq.getSession(false);
        if (session == null || session.getAttribute("currentUserId") == null) {
            throw new UnauthorizedException("未登录或会话已过期");
        }
        Long userId = (Long) session.getAttribute("currentUserId");
        AuthUser user = userRepository.findById(userId).orElseThrow(() -> new UnauthorizedException("未登录或会话已过期"));
        Map<String, Object> data = new HashMap<>();
        data.put("id", user.getId());
        data.put("lastLoginTime", user.getLastLoginTime());
        data.put("lastLoginIp", user.getLastLoginIp());
        return ApiResponse.success(data);
    }

    @PostMapping("/logout")
    public ApiResponse<Void> logout(HttpServletRequest httpReq) {
        HttpSession session = httpReq.getSession(false);
        if (session != null) {
            session.invalidate();
        }
        return ApiResponse.success("退出成功", null);
    }
}


