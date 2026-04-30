<script setup>
import { useRouter } from 'vue-router'
import { ref, onMounted } from 'vue'

const router = useRouter()
const errorCode = ref('404')
const backText = '返回首页'

const stars = ref([])
onMounted(() => {
  stars.value = Array.from({ length: 50 }, () => ({
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 3 + 1,
    opacity: Math.random() * 0.5 + 0.5,
    delay: Math.random() * 5
  }))
})
</script>

<template>
  <div class="not-found-container">
    <div class="stars">
      <div
          v-for="(star, index) in stars"
          :key="index"
          class="star"
          :style="{
          left: `${star.x}%`,
          top: `${star.y}%`,
          width: `${star.size}px`,
          height: `${star.size}px`,
          opacity: star.opacity,
          animationDelay: `${star.delay}s`
        }"
      ></div>
    </div>

    <div class="content">
      <div class="error-code" data-text="404">404</div>
      <h1 class="error-title">您访问的页面不存在</h1>

      <button
          @click="router.push('/')"
          class="home-button"
      >
        <span>{{ backText }}</span>
        <svg class="arrow" viewBox="0 0 24 24">
          <path d="M5 12H19M12 5L19 12L12 19" />
        </svg>
      </button>

      <div class="astronaut">
        <div class="helmet"></div>
        <div class="face">
          <div class="eyes">
            <div class="eye left"></div>
            <div class="eye right"></div>
          </div>
          <div class="mouth"></div>
        </div>
        <div class="body"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.not-found-container {
  position: relative;
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  color: white;
  font-family: 'Segoe UI', system-ui, sans-serif;
}

.stars {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.star {
  position: absolute;
  background-color: white;
  border-radius: 50%;
  animation: twinkle 3s infinite alternate;
}

@keyframes twinkle {
  0% { opacity: 0.3; }
  100% { opacity: 1; }
}

.content {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 2rem;
  max-width: 800px;
}

.error-code {
  font-size: 10rem;
  font-weight: 900;
  margin: 0;
  color: rgba(255, 255, 255, 0.1);
  position: relative;
  line-height: 1;
}

.error-code::before {
  content: attr(data-text);
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  color: #fff;
  overflow: hidden;
  animation: glitch 2s infinite linear alternate;
}

.error-title {
  font-size: 2.5rem;
  margin: 1rem 0;
  background: linear-gradient(90deg, #ff6b6b, #feca57);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.home-button {
  position: relative;
  display: inline-flex;
  align-items: center;
  padding: 0.8rem 2rem;
  background: linear-gradient(45deg, #6a11cb, #2575fc);
  color: white;
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.home-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

.home-button:active {
  transform: translateY(1px);
}

.home-button span {
  position: relative;
  z-index: 1;
  margin-right: 0.5rem;
}

.arrow {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: transform 0.3s ease;
}

.home-button:hover .arrow {
  transform: translateX(5px);
}

.astronaut {
  position: absolute;
  right: -100px;
  bottom: -50px;
  width: 200px;
  height: 200px;
  animation: float 6s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(5deg); }
  50% { transform: translateY(-20px) rotate(-5deg); }
}

@media (max-width: 768px) {
  .error-code {
    font-size: 6rem;
  }

  .error-title {
    font-size: 1.8rem;
  }

  .astronaut {
    width: 120px;
    height: 120px;
    right: -40px;
    bottom: -20px;
  }
}
</style>
