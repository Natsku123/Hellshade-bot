<template>
  <div class="levels">
    <v-row>
      <v-col md="12">
        <LevelsExpChart height="100" :options="chartOptions" :range="range" />
      </v-col>
    </v-row>
  </div>
</template>

<script>
import LevelsExpChart from "@/components/LevelsExpChart";
export default {
  name: 'Levels',
  components: {
    LevelsExpChart
  },
  data: () => ({
    chartOptions: {
      scales: {
        yAxes: [{
          id: 'A',
          type: 'linear',
          position: 'left',
        }, {
          id: 'B',
          type: 'linear',
          position: 'right',
          ticks: {
            min: 0,
            max: 15
          }
        }]
      }
    },
    range: {
      min: 0,
      max: 150
    }
  }),
}
</script>
