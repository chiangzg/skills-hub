<template>
  <div class="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  console.log('ready')
  console.log('~/skills')
})
</script>

<style>
:root {
  /* 主色调 - 深色科技风格 */
  --bg-primary: #0f0f1a;
  --bg-secondary: #1a1b26;
  --bg-tertiary: #252637;
  
  /* 文字颜色 */
  --text-primary: #e1e2f0;
  --text-secondary: #a9b1d6;
  --text-tertiary: #787c99;
  
  /* 品牌色 */
  --brand-blue: #7aa2f7;
  --brand-purple: #bb9af7;
  --brand-green: #9ece6a;
  --brand-yellow: #e0af68;
  --brand-red: #f7768e;
  --brand-cyan: #7dcfff;
  
  /* 边框和分割线 */
  --border-color: #414868;
  --border-light: #2d2e4a;
  
  /* 阴影效果 */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.2);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.25);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.3);
  
  /* 过渡动画 */
  --transition-fast: 0.15s ease;
  --transition-normal: 0.3s ease;
  --transition-slow: 0.5s ease;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  height: 100%;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', 'Monaco', monospace;
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
}

#app {
  min-height: 100vh;
}

.app {
  min-height: 100vh;
  background: var(--bg-primary);
  background-image: 
    radial-gradient(circle at 10% 20%, rgba(122, 162, 247, 0.1) 0%, transparent 20%),
    radial-gradient(circle at 90% 80%, rgba(187, 154, 247, 0.1) 0%, transparent 20%);
}

a {
  color: var(--brand-blue);
  text-decoration: none;
  transition: color var(--transition-fast);
}

a:hover {
  color: var(--brand-cyan);
  text-decoration: underline;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--brand-blue);
}
</style>
