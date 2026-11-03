<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { createElement } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { ExperimentCharts } from '../react/ExperimentCharts'
const props = defineProps<{ kind: 'tokens' | 'quality' | 'timeline' }>()
const host = ref<HTMLElement | null>(null)
let root: Root | undefined
const render = () => root?.render(createElement(ExperimentCharts, { kind: props.kind }))
onMounted(() => { if (host.value) { root = createRoot(host.value); render() } })
watch(() => props.kind, render)
onBeforeUnmount(() => root?.unmount())
</script>
<template><div ref="host" /></template>
