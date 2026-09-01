import { AppShell } from "./components/layout/AppShell";
import { HeroSection } from "./components/sections/HeroSection";
import { MetricGrid } from "./components/sections/MetricGrid";
import { ThresholdControls } from "./components/sections/ThresholdControls";
import { ItemsetSection } from "./components/sections/ItemsetSection";
import { RuleBoard } from "./components/sections/RuleBoard";
import { BasketExplorer } from "./components/sections/BasketExplorer";
import { MethodSection } from "./components/sections/MethodSection";
import { AsyncState } from "./components/ui/AsyncState";
import { useBasketSignals } from "./hooks/useBasketSignals";

export function App() {
  const dashboard = useBasketSignals();

  return (
    <AppShell status={dashboard.status}>
      <HeroSection />
      <AsyncState error={dashboard.dashboardError} onRetry={dashboard.retryDashboard} title="Unable to refresh mining evidence" />
      <MetricGrid summary={dashboard.summary} topRule={dashboard.rules[0]} />
      <ThresholdControls filters={dashboard.filters} summary={dashboard.summary} onChange={dashboard.setFilter} />
      <ItemsetSection
        rows={dashboard.itemsets}
        transactionCount={dashboard.summary?.transaction_count}
        size={dashboard.filters.size}
        onSizeChange={(size) => dashboard.setFilter("size", size)}
        loading={dashboard.loading}
      />
      <RuleBoard
        rows={dashboard.rules}
        transactionCount={dashboard.summary?.transaction_count}
        sort={dashboard.filters.sort}
        onSortChange={(sort) => dashboard.setFilter("sort", sort)}
        loading={dashboard.loading}
      />
      <BasketExplorer
        items={dashboard.items}
        selectedItem={dashboard.selectedItem}
        context={dashboard.context}
        onItemChange={dashboard.setSelectedItem}
        loading={dashboard.contextLoading}
        error={dashboard.contextError}
        onRetry={dashboard.retryContext}
      />
      <MethodSection />
    </AppShell>
  );
}
