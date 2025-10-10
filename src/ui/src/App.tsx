function App() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold">DocuSearch</h1>
          <p className="text-muted-foreground mt-2">Document Library - Wave 1 Foundation</p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="rounded-lg border bg-card p-8 text-center">
          <h2 className="text-2xl font-semibold mb-4">🚀 Foundation Ready</h2>
          <p className="text-muted-foreground">
            React + TypeScript + Vite + Tailwind CSS initialized successfully.
          </p>
          <p className="text-sm text-muted-foreground mt-4">
            Wave 1 in progress - Component stubs coming next
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;
