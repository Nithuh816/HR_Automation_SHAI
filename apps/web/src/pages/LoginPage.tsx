import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function LoginPage(): JSX.Element {
  return (
    <div className="grid min-h-screen place-items-center bg-background p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 grid h-10 w-10 place-items-center rounded-md bg-primary text-primary-foreground">
            <span className="font-bold">HR</span>
          </div>
          <CardTitle>SHAI · HR Automation</CardTitle>
          <CardDescription>Sign in with your Microsoft 365 account</CardDescription>
        </CardHeader>
        <CardContent>
          <Button className="w-full" disabled>
            Continue with Microsoft (wired in M1)
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
