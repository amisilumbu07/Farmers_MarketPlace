//! Shared, verifiable record of an order: commitment, attestation hash chain, final settlement.
//! Holds no personal data and moves no tokens; only hashes and a status. The marketplace authority signs.
use anchor_lang::prelude::*;
use anchor_lang::solana_program::hash::hashv;

// Local dev id (keypair in target/, git-ignored). Run `anchor keys sync` with your own keypair before a real deploy.
declare_id!("9ZZ5bejD4NdPr7zf9covKHDig6tcqh628Fdtrm4mT9MU");

pub const COMMITTED: u8 = 0;
pub const COMPLETED: u8 = 1;
pub const REFUNDED: u8 = 2;

#[program]
pub mod marketplace_settlement {
    use super::*;

    pub fn commit_order(ctx: Context<CommitOrder>, order_hash: [u8; 32], amount_minor: u64) -> Result<()> {
        let s = &mut ctx.accounts.settlement;
        s.authority = ctx.accounts.authority.key();
        s.order_hash = order_hash;
        s.amount_minor = amount_minor;
        s.status = COMMITTED;
        s.attestation_count = 0;
        s.attestation_chain = [0; 32];
        s.bump = ctx.bumps.settlement;
        Ok(())
    }

    /// chain = sha256(chain || attestation_hash): order and content of the evidence are both fixed.
    /// `expected_count` is the slot this hash must take, so a retried transaction that already landed is refused
    /// (UnexpectedCount) instead of appending the same evidence twice.
    pub fn record_attestation(ctx: Context<Update>, attestation_hash: [u8; 32], expected_count: u32) -> Result<()> {
        let s = &mut ctx.accounts.settlement;
        require!(s.status == COMMITTED, SettlementError::AlreadySettled);
        require!(s.attestation_count == expected_count, SettlementError::UnexpectedCount);
        s.attestation_chain = hashv(&[&s.attestation_chain, &attestation_hash]).to_bytes();
        s.attestation_count += 1;
        Ok(())
    }

    pub fn settle(ctx: Context<Update>, outcome: u8) -> Result<()> {
        let s = &mut ctx.accounts.settlement;
        require!(s.status == COMMITTED, SettlementError::AlreadySettled);
        require!(outcome == COMPLETED || outcome == REFUNDED, SettlementError::BadOutcome);
        s.status = outcome;
        Ok(())
    }
}

#[derive(Accounts)]
#[instruction(order_hash: [u8; 32])]
pub struct CommitOrder<'info> {
    #[account(init, payer = authority, space = 8 + Settlement::SIZE, seeds = [b"settlement", order_hash.as_ref()], bump)]
    pub settlement: Account<'info, Settlement>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Update<'info> {
    #[account(mut, seeds = [b"settlement", settlement.order_hash.as_ref()], bump = settlement.bump, has_one = authority)]
    pub settlement: Account<'info, Settlement>,
    pub authority: Signer<'info>,
}

#[account]
pub struct Settlement {
    pub authority: Pubkey,
    pub order_hash: [u8; 32],
    pub amount_minor: u64,
    pub status: u8,
    pub attestation_count: u32,
    pub attestation_chain: [u8; 32],
    pub bump: u8,
}

impl Settlement {
    pub const SIZE: usize = 32 + 32 + 8 + 1 + 4 + 32 + 1;
}

#[error_code]
pub enum SettlementError {
    #[msg("Order already settled")]
    AlreadySettled,
    #[msg("Outcome must be 1 (completed) or 2 (refunded)")]
    BadOutcome,
    #[msg("Attestation position already taken or out of order")]
    UnexpectedCount,
}
