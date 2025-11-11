<template>
  <div class="login-container">
    <div class="login-box">
      <div class="title">
        <h1>手写数字识别系统</h1>
        <p>请登录以继续</p>
      </div>
      <form @submit.prevent="handleLogin">
        <div v-if="error" class="error-message">{{ error }}</div>
        <div class="input-group">
          <label for="username">用户ID</label>
          <input type="number" id="username" v-model="username" placeholder="请输入用户ID（数字）" required>
        </div>
        <div class="input-group">
          <label for="password">密码</label>
          <input type="password" id="password" v-model="password" placeholder="请输入密码" required>
        </div>
        <div class="input-group captcha-group">
          <div class="captcha-input">
            <label for="captcha">验证码</label>
            <input type="text" id="captcha" v-model="captchaCode" placeholder="请输入验证码" required>
          </div>
          <div class="captcha-image" @click="fetchCaptcha">
            <img v-if="captchaUrl" :src="captchaUrl" alt="验证码">
            <span v-else>加载中...</span>
          </div>
        </div>
        <button type="submit" class="btn-login" :disabled="loading">
          {{ loading ? '登录中...' : '登 录' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { login, getCaptcha, addLog } from '@/services/api';

const username = ref('');
const password = ref('');
const captchaCode = ref('');
const captchaId = ref('');
const captchaUrl = ref('');
const error = ref('');
const loading = ref(false);
const router = useRouter();

const fetchCaptcha = async () => {
  try {
    const response = await getCaptcha();
    if (response.data.code === 200) {
      captchaId.value = response.data.data.verifyCodeId;
      captchaUrl.value = response.data.data.verifyCodeImgBase64;
      error.value = '';
    } else {
      error.value = response.data.msg || '验证码加载失败';
    }
  } catch (err: any) {
    error.value = '验证码加载失败，请刷新重试。';
    console.error(err);
    // 如果后端未启动，使用模拟验证码
    if (err.code === 'ECONNREFUSED' || err.message?.includes('Network Error')) {
      captchaId.value = 'mock-captcha-id-' + Date.now();
      captchaUrl.value = `https://via.placeholder.com/120x40.png?text=1234`;
    }
  }
};

onMounted(() => {
  fetchCaptcha();
});

const handleLogin = async () => {
  if (!username.value || !password.value || !captchaCode.value) {
    error.value = '所有字段均为必填项';
    return;
  }
  
  // 将用户名转换为数字 ID（后端要求 userid 为 Long 类型）
  const userid = parseInt(username.value);
  if (isNaN(userid)) {
    error.value = '用户名必须是数字 ID';
    return;
  }
  
  loading.value = true;
  error.value = '';
  
  try {
          const response = await login(userid, password.value, captchaCode.value, captchaId.value);
          if (response.data.code === 200) {
            // 登录成功，使用 Session（后端已设置）
            localStorage.setItem('authToken', 'authenticated');
            localStorage.setItem('userId', String(response.data.data.user.id));
            error.value = '';
            // 记录登录日志
            await addLog(`登录系统`);
            router.push('/datasets');
          } else {
      error.value = response.data.msg || '登录失败';
      fetchCaptcha(); // 登录失败后刷新验证码
    }
  } catch (err: any) {
    if (err.response?.data?.msg) {
      error.value = err.response.data.msg;
    } else {
      error.value = '登录失败，请检查您的输入。';
    }
    console.error(err);
    fetchCaptcha(); // 登录失败后刷新验证码
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f4f7f9;
}

.login-box {
  width: 400px;
  padding: 3rem;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  border: 1px solid #e0e0e0;
}

.title {
  text-align: center;
  margin-bottom: 2rem;
}

.title h1 {
  font-size: 1.8rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.title p {
  color: #7f8c8d;
  margin-top: 0.5rem;
}

.input-group {
  margin-bottom: 1.5rem;
}

.input-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #34495e;
}

.input-group input {
  width: 100%;
  padding: 0.8rem 1rem;
  border: 1px solid #bdc3c7;
  border-radius: 5px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.input-group input:focus {
  outline: none;
  border-color: #1abc9c;
}

.captcha-group {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
}

.captcha-input {
  flex-grow: 1;
}

.captcha-image {
  height: 45px; /* 与输入框高度大致对齐 */
  width: 120px;
  border: 1px solid #bdc3c7;
  border-radius: 5px;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #ecf0f1;
}

.captcha-image img {
  max-width: 100%;
  max-height: 100%;
  border-radius: 4px;
}

.btn-login {
  width: 100%;
  padding: 0.9rem;
  border: none;
  border-radius: 5px;
  background-color: #2c3e50;
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-login:hover:not(:disabled) {
  background-color: #34495e;
}

.btn-login:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
  opacity: 0.7;
}

.error-message {
  background-color: #fce8e6;
  color: #d93025;
  border: 1px solid #d93025;
  border-radius: 5px;
  padding: 0.8rem;
  margin-bottom: 1.5rem;
  text-align: center;
}
</style>
