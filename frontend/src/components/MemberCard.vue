<template>
  <v-card>
    <v-card-title class="title">{{ member.player.name }}</v-card-title>
    <v-card-subtitle v-if="member.server">{{
      member.server.name
    }}</v-card-subtitle>
    <div v-if="nextLevel" class="text-left px-2">
      <v-row>
        <v-col v-if="member.level" md="auto"
          ><strong>Level {{ member.level.value }}</strong></v-col
        >
        <v-col v-else md="auto">Level 0</v-col>
        <v-spacer />
        <v-col md="auto"
          >{{ nextLevel.exp - member.exp }} exp to
          <strong>Level {{ nextLevel.value }}</strong></v-col
        >
      </v-row>
      <v-row>
        <v-col>
          <v-progress-linear
            rounded
            height="15"
            :value="(member.exp / nextLevel.exp) * 100"
          >
            <template v-slot:default="{ value }">
              <strong>{{ Math.ceil(value) }}%</strong>
            </template>
          </v-progress-linear>
        </v-col>
      </v-row>
      <v-row
        ><v-col md="auto"
          ><strong>{{ member.exp }} exp</strong></v-col
        ></v-row
      >
    </div>
  </v-card>
</template>

<script>
import { gql } from "graphql-request";
import { client } from "@/utils";

export default {
  name: "MemberCard",
  props: {
    member: Object
  },
  data: () => ({
    nextLevel: null,
    loading: true
  }),
  mounted() {
    let current = 0;
    if (this.member.level) {
      current = this.member.level.value;
    }

    const query = gql`
        {
            level(value: ${current + 1}) {
                uuid
                value
                exp
            }
        }
      `;
    client
      .request(query)
      .then(data => {
        data["level"][0].uuid = data["level"][0].uuid.substring(
          1,
          data["level"][0].uuid.length - 1
        );
        this.nextLevel = data["level"][0];
        this.loading = false;
      })
      .catch(() => {
        this.loading = false;
      });
  }
};
</script>

<style scoped></style>
