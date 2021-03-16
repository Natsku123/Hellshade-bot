<template>
  <div class="server">
    <v-row justify="center"
      ><v-col
        ><h1>{{ server.name }}</h1></v-col
      ></v-row
    >
    <v-row justify="center"
      ><v-col><h2>Top 10</h2></v-col></v-row
    >
    <v-row>
      <v-col
        xs="12"
        sm="12"
        md="4"
        lg="3"
        v-for="member in top10"
        :key="member.uuid"
        class=""
      >
        <MemberCard :member="member" />
      </v-col>
    </v-row>
    <v-row justify="center"
      ><v-col><h2>All Members</h2></v-col></v-row
    >
    <v-row>
      <v-col
        xs="12"
        sm="12"
        md="4"
        lg="3"
        v-for="member in members"
        :key="member.uuid"
        class=""
      >
        <MemberCard :member="member" />
      </v-col>
    </v-row>
  </div>
</template>

<script>
import { client } from "@/utils";
import { gql } from "graphql-request";
import MemberCard from "@/components/MemberCard";
import { reloadMixin } from "@/mixins/reloadMixin";

export default {
  name: "Server",
  components: { MemberCard },
  mixins: [reloadMixin],
  data: () => ({
    server: {
      name: "Loading...",
      uuid: ""
    },
    members: [],
    top10: [],
    loading: true
  }),
  methods: {
    loadContent() {
      const id = this.$route.params["id"];
      const serverQuery = gql`
        {
            server(uuid: \"${id}\") {
                uuid
                name
            }
        }
      `;

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
                }
                exp
            }
        }
      `;

      client
        .request(serverQuery)
        .then(data => {
          data["server"][0].uuid = data["server"][0].uuid.substring(
            1,
            data["server"][0].uuid.length - 1
          );
          this.server = data["server"][0];
          this.loading = false;
        })
        .catch(() => {
          this.loading = false;
        });

      client.request(membersQuery).then(data => {
        data.member.forEach(member => {
          member.uuid = member.uuid.substring(1, member.uuid.length - 1);
        });
        this.members = data.member.filter(
          member => !member.player.hidden && member.player.name !== "UNKNOWN"
        );
        this.members.sort((a, b) => {
          if (a.player.name < b.player.name) {
            return -1;
          } else if (a.player.name > b.player.name) {
            return 1;
          } else {
            return 0;
          }
        });
        this.top10 = data.member
          .sort((a, b) => {
            if (a.level === null && b.level !== null) {
              return 1;
            } else if (a.level !== null && b.level === null) {
              return -1;
            } else if (a.level === null && b.level === null) {
              return 0;
            } else if (a.level.value < b.level.value) {
              return 1;
            } else if (a.level.value > b.level.value) {
              return -1;
            } else if (a.exp < b.exp) {
              return 1;
            } else if (a.exp > b.exp) {
              return -1;
            } else {
              return 0;
            }
          })
          .slice(0, 10);
      });
    }
  }
};
</script>

<style scoped></style>
