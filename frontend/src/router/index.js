import Vue from "vue";
import VueRouter from "vue-router";
import Home from "../views/Home.vue";
import Levels from "@/views/Levels";
import Members from "@/views/Members";
import Servers from "@/views/Servers";
import Server from "@/views/Server";
import NotFound from "@/views/NotFound";

Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    name: "Home",
    component: Home
  },
  {
    path: "/about",
    name: "About",
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () =>
      import(/* webpackChunkName: "about" */ "../views/About.vue")
  },
  {
    path: "/levels",
    name: "Levels",
    component: Levels
  },
  {
    path: "/members",
    name: "Members",
    component: Members
  },
  {
    path: "/servers",
    name: "Servers",
    component: Servers
  },
  {
    path: "/servers/:id",
    name: "Server",
    component: Server
  },
  {
    path: "*",
    component: NotFound
  }
];

const router = new VueRouter({
  mode: "history",
  base: process.env.BASE_URL,
  routes
});

export default router;
