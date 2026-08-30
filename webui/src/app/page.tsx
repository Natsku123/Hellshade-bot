import Link from "next/link";
import { Server, Star, Users } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const links = [
  { href: "/servers", label: "Servers", description: "Browse connected Discord servers", icon: Server },
  { href: "/levels", label: "Levels", description: "See level and experience progression", icon: Star },
  { href: "/members", label: "Members", description: "Look up player stats", icon: Users },
];

export default function Home() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <div className="mb-8 flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Hellshade Bot Dashboard</h1>
        <p className="text-muted-foreground">
          Server activity, member levels and experience for Hellshade-bot.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {links.map(({ href, label, description, icon: Icon }) => (
          <Card key={href}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Icon className="size-5 text-primary" />
                {label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="mb-4 text-sm text-muted-foreground">{description}</p>
              <Button asChild size="sm">
                <Link href={href}>View {label}</Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
