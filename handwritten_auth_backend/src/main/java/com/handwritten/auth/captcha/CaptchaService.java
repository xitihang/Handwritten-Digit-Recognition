package com.handwritten.auth.captcha;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.Base64;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class CaptchaService {

    private static class CaptchaRecord {
        final String code;
        final Instant expireAt;

        CaptchaRecord(String code, Instant expireAt) {
            this.code = code;
            this.expireAt = expireAt;
        }
    }

    private final Map<String, CaptchaRecord> store = new ConcurrentHashMap<>();

    @Value("${app.captcha.length:4}")
    private int codeLength;

    @Value("${app.captcha.expire-minutes:5}")
    private int expireMinutes;

    public CaptchaResult generateCaptcha() {
        String code = randomCode(codeLength);
        String id = UUID.randomUUID().toString();
        Instant expireAt = Instant.now().plusSeconds(expireMinutes * 60L);
        store.put(id, new CaptchaRecord(code, expireAt));

        String base64 = createImageBase64(code);
        ZonedDateTime zdt = ZonedDateTime.ofInstant(expireAt, ZoneId.systemDefault());
        return new CaptchaResult(id, base64, zdt);
    }

    public boolean validate(String verifyCodeId, String inputCode) {
        cleanup();
        CaptchaRecord rec = store.get(verifyCodeId);
        if (rec == null) return false;
        if (rec.expireAt.isBefore(Instant.now())) {
            store.remove(verifyCodeId);
            return false;
        }
        boolean ok = rec.code.equalsIgnoreCase(inputCode);
        store.remove(verifyCodeId);
        return ok;
    }

    private void cleanup() {
        Instant now = Instant.now();
        store.entrySet().removeIf(e -> e.getValue().expireAt.isBefore(now));
    }

    private String randomCode(int len) {
        String chars = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789";
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < len; i++) {
            int idx = (int) (Math.random() * chars.length());
            sb.append(chars.charAt(idx));
        }
        return sb.toString();
    }

    private String createImageBase64(String code) {
        int width = 120, height = 40;
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = image.createGraphics();
        g.setColor(Color.WHITE);
        g.fillRect(0, 0, width, height);
        g.setFont(new Font("Arial", Font.BOLD, 24));
        g.setColor(Color.BLACK);
        g.drawString(code, 15, 28);
        g.dispose();
        try {
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            ImageIO.write(image, "png", baos);
            String base64 = Base64.getEncoder().encodeToString(baos.toByteArray());
            return "data:image/png;base64," + base64;
        } catch (Exception e) {
            throw new RuntimeException("验证码图片生成失败");
        }
    }

    public static class CaptchaResult {
        public final String verifyCodeId;
        public final String verifyCodeImgBase64;
        public final ZonedDateTime expireTime;

        public CaptchaResult(String verifyCodeId, String verifyCodeImgBase64, ZonedDateTime expireTime) {
            this.verifyCodeId = verifyCodeId;
            this.verifyCodeImgBase64 = verifyCodeImgBase64;
            this.expireTime = expireTime;
        }
    }
}


