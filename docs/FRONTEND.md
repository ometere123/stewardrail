# Frontend contract

The UI is a Next.js App Router control plane with task-specific routes for workspace, threshold charter governance, spend request/case inspection, issuer evidence, appeal court, custody, verification and reviewer docs.

Wallet policy is intentionally narrow: injected EIP-1193 only. No third-party wallet orchestration, embedded wallet, burner key, hardcoded account or application backend. Every signing action is hard-blocked unless the provider reports chain id 61999. Account and chain changes are subscribed globally.

Transaction UX distinguishes submitted, decided and finalized states and also checks the execution result. Consensus acceptance by itself is never displayed as application success.

Before final submission, the completion agent must add persistence/recovery for an already-submitted transaction hash across page refresh, bind the final deployed addresses, and run browser tests for wrong-network rejection, wallet rejection, account/chain changes, refresh recovery and execution failure.
