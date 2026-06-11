<script setup lang="ts">
import VisitorReportPanel from '../components/dashboard/VisitorReportPanel.vue';
</script>

<template>
  <section class="dashboard-main visitor-report-page">
    <div class="dashboard-title-row">
      <div>
        <h2>游客感受度报告</h2>
        <p>分析游客交互记录，生成关注点、情感趋势、服务建议和处理待办。</p>
      </div>
    </div>
    <VisitorReportPanel />
  </section>
</template>
