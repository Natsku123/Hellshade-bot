import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LevelPoint, MemberView } from "@/lib/types";

export function MemberCard({
  member,
  serverName,
  nextLevel,
}: {
  member: MemberView;
  serverName?: string;
  nextLevel?: LevelPoint | null;
}) {
  const levelValue = member.level ? member.level.value : 0;
  const progress = nextLevel && nextLevel.exp > 0
    ? Math.min(100, Math.round((member.exp / nextLevel.exp) * 100))
    : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{member.player.name}</CardTitle>
        <p className="text-sm text-muted-foreground">
          Level {levelValue}
          {serverName ? (
            <>
              {" "}at <span className="font-medium text-foreground">{serverName}</span>
            </>
          ) : null}
        </p>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between text-sm">
          <span className="font-semibold">{member.exp} exp</span>
          {nextLevel ? (
            <span className="text-muted-foreground">
              {Math.max(0, nextLevel.exp - member.exp)} exp to Level {nextLevel.value}
            </span>
          ) : null}
        </div>
        {progress !== null ? (
          <div className="mt-2 h-3 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
