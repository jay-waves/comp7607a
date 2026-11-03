<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { createElement } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { ObservationDemo } from '../react/ObservationDemo'
const host = ref<HTMLElement | null>(null)
let root: Root | undefined
onMounted(() => {
  if (host.value) {
    root = createRoot(host.value)
    root.render(createElement(ObservationDemo))
  }
})
onBeforeUnmount(() => root?.unmount())
</script>
<template><div ref="host" class="react-host" /></template>
