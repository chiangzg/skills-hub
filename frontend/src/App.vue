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
.app {
  min-height: 100vh;
  background: #1a1b26;
}

a {
  color: #7aa2f7;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
</style>
