package com.handwritten.auth.user;

import com.handwritten.auth.user.entity.AuthUser;
import com.handwritten.auth.user.repo.AuthUserRepository;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Component
public class UserDataInitializer {

    @Autowired
    private AuthUserRepository userRepository;

    @PostConstruct
    public void init() {
        // 如果用户不存在，创建默认管理员用户
        if (!userRepository.existsById(1L)) {
            AuthUser admin = new AuthUser();
            admin.setId(1L);
            admin.setPassword("admin"); // 默认密码，生产环境应使用加密
            userRepository.save(admin);
            System.out.println("已创建默认管理员用户: ID=1, 密码=admin");
        }
    }
}

