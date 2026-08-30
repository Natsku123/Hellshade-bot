import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">About Hellshade-bot</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 text-sm text-muted-foreground">
          <p>
            Hellshade-bot is a multi-purpose Discord bot. This dashboard shows
            server activity, member experience and level progression tracked
            by the bot.
          </p>
          <p>
            Source code is available on{" "}
            <a
              href="https://github.com/Natsku123/Hellshade-bot"
              target="_blank"
              rel="noreferrer"
              className="text-primary hover:underline"
            >
              GitHub
            </a>
            .
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
