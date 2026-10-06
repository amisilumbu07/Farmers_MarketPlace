//! In-memory tests of the compiled program (target/deploy/marketplace_settlement.so). Rebuild it first: `anchor build --no-idl`.
use litesvm::LiteSVM;
use sha2::{Digest, Sha256};
use solana_sdk::{
    instruction::{AccountMeta, Instruction, InstructionError},
    pubkey::Pubkey,
    signature::{Keypair, Signer},
    system_program,
    transaction::{Transaction, TransactionError},
};
use std::str::FromStr;

const ALREADY_SETTLED: u32 = 6000;
const BAD_OUTCOME: u32 = 6001;
const UNEXPECTED_COUNT: u32 = 6002;
const STATUS: usize = 80; // 8-byte Anchor tag + authority 32 + order_hash 32 + amount 8
const COUNT: std::ops::Range<usize> = 81..85;
const CHAIN: std::ops::Range<usize> = 85..117;

struct Chain {
    svm: LiteSVM,
    program: Pubkey,
    authority: Keypair,
    order: [u8; 32],
    account: Pubkey,
}

fn sha(parts: &[&[u8]]) -> [u8; 32] {
    let mut h = Sha256::new();
    parts.iter().for_each(|p| h.update(p));
    h.finalize().into()
}

fn data(name: &str, args: &[&[u8]]) -> Vec<u8> {
    let mut d = sha(&[format!("global:{name}").as_bytes()])[..8].to_vec();
    args.iter().for_each(|a| d.extend_from_slice(a));
    d
}

impl Chain {
    fn new(order: &str) -> Chain {
        let program = Pubkey::from_str("9ZZ5bejD4NdPr7zf9covKHDig6tcqh628Fdtrm4mT9MU").unwrap();
        let mut svm = LiteSVM::new();
        svm.add_program_from_file(program, concat!(env!("CARGO_MANIFEST_DIR"), "/../target/deploy/marketplace_settlement.so")).expect("build the program first");
        let authority = Keypair::new();
        svm.airdrop(&authority.pubkey(), 10_000_000_000).unwrap();
        let order = sha(&[order.as_bytes()]);
        let account = Pubkey::find_program_address(&[b"settlement", &order], &program).0;
        Chain { svm, program, authority, order, account }
    }

    fn send(&mut self, signer: &Keypair, name: &str, args: &[&[u8]], creates: bool) -> Result<(), TransactionError> {
        let mut accounts = vec![AccountMeta::new(self.account, false), AccountMeta::new(signer.pubkey(), true)];
        if creates {
            accounts.push(AccountMeta::new_readonly(system_program::id(), false));
        }
        let ix = Instruction::new_with_bytes(self.program, &data(name, args), accounts);
        self.svm.expire_blockhash(); // an identical retry must not be dropped as a duplicate
        let tx = Transaction::new_signed_with_payer(&[ix], Some(&signer.pubkey()), &[signer], self.svm.latest_blockhash());
        self.svm.send_transaction(tx).map(|_| ()).map_err(|e| e.err)
    }

    fn commit(&mut self) -> Result<(), TransactionError> {
        let (order, authority) = (self.order, Keypair::from_bytes(&self.authority.to_bytes()).unwrap());
        self.send(&authority, "commit_order", &[&order, &1250u64.to_le_bytes()], true)
    }

    fn attest(&mut self, hash: [u8; 32], position: u32) -> Result<(), TransactionError> {
        let authority = Keypair::from_bytes(&self.authority.to_bytes()).unwrap();
        self.send(&authority, "record_attestation", &[&hash, &position.to_le_bytes()], false)
    }

    fn settle(&mut self, outcome: u8) -> Result<(), TransactionError> {
        let authority = Keypair::from_bytes(&self.authority.to_bytes()).unwrap();
        self.send(&authority, "settle", &[&[outcome]], false)
    }

    fn bytes(&self) -> Vec<u8> {
        self.svm.get_account(&self.account).expect("order account").data
    }
}

fn refused(result: Result<(), TransactionError>, code: u32) {
    assert_eq!(result, Err(TransactionError::InstructionError(0, InstructionError::Custom(code))));
}

#[test]
fn full_lifecycle_records_a_hash_chain_and_settles() {
    let mut c = Chain::new("ord_1");
    c.commit().unwrap();
    assert_eq!((c.bytes().len(), c.bytes()[STATUS]), (118, 0));
    let (h0, h1) = (sha(&[b"pickup"]), sha(&[b"delivery"]));
    c.attest(h0, 0).unwrap();
    c.attest(h1, 1).unwrap();
    c.settle(1).unwrap();
    let b = c.bytes();
    assert_eq!(b[STATUS], 1);
    assert_eq!(b[COUNT], 2u32.to_le_bytes());
    assert_eq!(b[CHAIN], sha(&[&sha(&[&[0u8; 32], &h0]), &h1])); // chain = sha256(chain || hash), order and content both fixed
}

#[test]
fn committing_the_same_order_twice_is_refused() {
    let mut c = Chain::new("ord_2");
    c.commit().unwrap();
    assert!(c.commit().is_err());
}

#[test]
fn a_retried_or_skipped_attestation_slot_is_refused() {
    let mut c = Chain::new("ord_3");
    c.commit().unwrap();
    let h = sha(&[b"pickup"]);
    c.attest(h, 0).unwrap();
    refused(c.attest(h, 0), UNEXPECTED_COUNT); // lost-reply retry: already landed
    refused(c.attest(h, 5), UNEXPECTED_COUNT); // out of order
    assert_eq!(c.bytes()[COUNT], 1u32.to_le_bytes());
}

#[test]
fn nothing_changes_after_settlement() {
    let mut c = Chain::new("ord_4");
    c.commit().unwrap();
    c.settle(2).unwrap();
    refused(c.attest(sha(&[b"late"]), 0), ALREADY_SETTLED);
    refused(c.settle(1), ALREADY_SETTLED);
    assert_eq!(c.bytes()[STATUS], 2);
}

#[test]
fn only_outcomes_1_and_2_are_accepted() {
    let mut c = Chain::new("ord_5");
    c.commit().unwrap();
    refused(c.settle(0), BAD_OUTCOME);
    refused(c.settle(3), BAD_OUTCOME);
    assert_eq!(c.bytes()[STATUS], 0);
}

#[test]
fn another_signer_cannot_write_to_the_order() {
    let mut c = Chain::new("ord_6");
    c.commit().unwrap();
    let stranger = Keypair::new();
    c.svm.airdrop(&stranger.pubkey(), 1_000_000_000).unwrap();
    assert!(c.send(&stranger, "settle", &[&[1]], false).is_err());
    assert_eq!(c.bytes()[STATUS], 0);
}
