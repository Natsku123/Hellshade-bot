<template>
  <div class="server">
    <h1> {{ server.name }}</h1>
    <p v-for="member in members" :key="member.uuid">{{ member }}</p>
  </div>
</template>

<script>
import { client } from "@/utils";
import {gql} from "graphql-request";

export default {
  name: "Server",
  data: () => ({
    server: {
      name: "Loading...",
      uuid: ""
    },
    members: [],
    loading: true
  }),
  methods: {
    loadContent() {
      const id = this.$route.params['id'];
      const serverQuery = gql`
        {
            server(uuid: \"${id}\") {
                uuid
                name
            }
        }
      `

      const membersQuery = gql`
        {
            member(serverUuid: \"${id}\") {
                uuid
                player {
                    uuid
                    name
                    hidden
                }
                level {
                    uuid
                    value
                    exp
                }
                exp
            }
        }
      `

      client.request(serverQuery).then((data) => {
        data['server'][0].uuid = data['server'].uuid.substring(1, data['server'].uuid.length-1);
        this.server = data['server'];
        this.loading = false;
      }).catch(() => {
        this.loading = false;
      });

      client.request(membersQuery).then((data) => {
        data.member.forEach((member) => {
          member.uuid = member.uuid.substring(1, member.uuid.length-1);
        });
        this.members = data.member.filter(member => !member.player.hidden);
      })
    }
  },
  mounted() {
    this.loadContent();
  }
}
</script>

<style scoped>

</style>