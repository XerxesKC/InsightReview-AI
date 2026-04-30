<template>
  <div class="markdown-body" v-html="rendered"></div>
</template>

<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const props = defineProps({
  content: {
    type: String,
    default: ''
  }
})

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
})

const rendered = computed(() => {
  return md.render(props.content || '')
})
</script>

<style scoped>

.markdown-body {
  font-size: 14px;
  line-height: 1.8;
}
.markdown-body h1,
.markdown-body h2,
.markdown-body h3 {
  margin: 0.8em 0 0.4em;
  font-weight: 600;
}
.markdown-body p {
  margin: 0.4em 0;
}
.markdown-body ul,
.markdown-body ol {
  padding-left: 1.4em;
  margin: 0.4em 0;
}
.markdown-body code {
  padding: 0.1em 0.25em;
  border-radius: 4px;
  background-color: rgba(15, 23, 42, 0.06);
}
.markdown-body pre code {
  padding: 0;
  background-color: transparent;
}
.markdown-body pre {
  padding: 10px 12px;
  border-radius: 8px;
  background-color: #020617;
  color: #e5e7eb;
  overflow: auto;
}
</style>