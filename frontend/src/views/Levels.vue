<template>
  <div class="levels">
    <v-row>
      <v-col md="12">
        <LevelsExpChart :height="100" :options="chartOptions" :range="range" />
      </v-col>
    </v-row>
    <v-row>
      <v-col md="12">
        <v-text-field
          v-model="range[1]"
          single-line
          type="number"
          label="Levels"
        />
      </v-col>
    </v-row>
  </div>
</template>

<script>
import LevelsExpChart from "@/components/LevelsExpChart";
import { reloadMixin } from "@/mixins/reloadMixin";

export default {
  name: "Levels",
  components: {
    LevelsExpChart
  },
  mixins: [reloadMixin],
  data: () => ({
    chartOptions: {
      scales: {
        yAxes: [
          {
            id: "A",
            type: "linear",
            position: "left"
          },
          {
            id: "B",
            type: "linear",
            position: "right",
            ticks: {
              min: 0,
              max: 15
            }
          }
        ]
      }
    },
    range: [0, 150]
  })
};
</script>
