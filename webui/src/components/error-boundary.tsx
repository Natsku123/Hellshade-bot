"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: (error: Error, retry: () => void) => React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  retry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.retry);
      }

      return (
        <div className="mx-auto max-w-md px-4 py-10">
          <Card>
            <CardHeader>
              <CardTitle className="text-destructive">Something went wrong</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <p className="text-sm text-muted-foreground">
                {this.state.error.message}
              </p>
              <div className="text-xs text-muted-foreground">
                <details className="cursor-pointer">
                  <summary>Error details</summary>
                  {process.env.NODE_ENV !== "production" ? (
                    <pre className="mt-2 overflow-auto rounded bg-muted p-2 text-xs">
                      {this.state.error.stack}
                    </pre>
                  ) : null}
                </details>
              </div>
              <Button onClick={this.retry} size="sm">
                Try again
              </Button>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Hook for handling async errors in components
 */
export function useAsyncError() {
  const [, setError] = React.useState();

  return React.useCallback(
    (error: Error) => {
      setError(() => {
        throw error;
      });
    },
    [setError],
  );
}

/**
 * Hook for handling API errors
 */
export function useApiError() {
  const throwError = useAsyncError();

  return React.useCallback(
    (error: unknown) => {
      const message =
        error instanceof Error ? error.message : "An unknown error occurred";
      throwError(new Error(`API Error: ${message}`));
    },
    [throwError],
  );
}
