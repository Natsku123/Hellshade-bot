<template>
  <v-app>
    <v-navigation-drawer app>
      <v-list-item>
        <v-list-item-content>
          <v-list-item-title class="title">
            Hellshade-bot
          </v-list-item-title>
          <v-list-item-subtitle>
            Multi-purpose Discord bot
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>

      <v-divider />
      <v-list dense nav>
        <v-list-item link to="/">
          <v-list-item-icon><v-icon>mdi-home</v-icon></v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Home</v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <v-list-item link to="/about">
          <v-list-item-icon><v-icon>mdi-information</v-icon></v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>About</v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <v-list-item link to="/servers">
          <v-list-item-icon><v-icon>mdi-server</v-icon></v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Servers</v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <v-list-item link to="/levels">
          <v-list-item-icon><v-icon>mdi-star</v-icon></v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Levels</v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <v-list-item link to="/members">
          <v-list-item-icon
            ><v-icon>mdi-account-group</v-icon></v-list-item-icon
          >
          <v-list-item-content>
            <v-list-item-title>Members</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item link href="https://github.com/Natsku123/Hellshade-bot">
          <v-list-item-icon>
            <v-icon>mdi-github</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Github</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
      </v-list>
      <v-spacer />
      <v-row class="mx-2">
        <v-col>
          <v-switch v-model="dark" label="Dark Mode"></v-switch>
        </v-col>
      </v-row>
    </v-navigation-drawer>

    <v-app-bar dense flat class="hidden-md-and-up">
      <v-app-bar-nav-icon @click="mobileDrawer = true">
        <v-icon>mdi-menu</v-icon>
      </v-app-bar-nav-icon>
      <v-app-bar-title>Hellshade-bot</v-app-bar-title>
    </v-app-bar>
    <v-navigation-drawer
      class="hidden-md-and-up"
      v-model="mobileDrawer"
      absolute
      temporary
    >
      <v-list nav dense>
        <v-list-item-group v-model="mobileGroup">
          <v-list-item link to="/">
            <v-list-item-icon><v-icon>mdi-home</v-icon></v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>Home</v-list-item-title>
            </v-list-item-content>
          </v-list-item>

          <v-list-item link to="/about">
            <v-list-item-icon>
              <v-icon>mdi-information</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>About</v-list-item-title>
            </v-list-item-content>
          </v-list-item>

          <v-list-item link to="/servers">
            <v-list-item-icon><v-icon>mdi-server</v-icon></v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>Servers</v-list-item-title>
            </v-list-item-content>
          </v-list-item>

          <v-list-item link to="/levels">
            <v-list-item-icon><v-icon>mdi-star</v-icon></v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>Levels</v-list-item-title>
            </v-list-item-content>
          </v-list-item>

          <v-list-item link to="/members">
            <v-list-item-icon>
              <v-icon>mdi-account-group</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>Members</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
          <v-list-item link href="https://github.com/Natsku123/Hellshade-bot">
            <v-list-item-icon>
              <v-icon>mdi-github</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>Github</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list-item-group>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <v-container fluid>
        <router-view></router-view>
      </v-container>
    </v-main>

    <v-footer app>
      <v-row justify="center">
        <v-col md="auto">Hellshade-bot {{ new Date().getFullYear() }}</v-col>
      </v-row>
    </v-footer>
  </v-app>
</template>

<script>
export default {
  name: "App",
  data: () => ({
    mobileDrawer: false,
    mobileGroup: null
  }),
  computed: {
    dark: {
      set(value) {
        this.$vuetify.theme.dark = value;
        localStorage.setItem("dark", value.toString());
      },
      get() {
        return localStorage.getItem("dark") === "true";
      }
    }
  },
  mounted() {
    const current = localStorage.getItem("dark");
    this.$vuetify.theme.dark = current === "true";
  }
};
</script>

<style lang="scss">
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
}

#nav {
  padding: 30px;

  a {
    font-weight: bold;
    color: #2c3e50;

    &.router-link-exact-active {
      color: #42b983;
    }
  }
}
</style>
