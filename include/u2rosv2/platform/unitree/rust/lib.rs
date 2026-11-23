//! Guest-side codec for the Unitree Go2 low-state attachment.
#![no_std]

#[derive(Debug, Copy, Clone, PartialEq)]
pub struct LowState {
    pub tick: u32,
    pub first_joint_position: f32,
}

/// Encode the complete driver.submit envelope for one 16-byte buffer.read.
pub fn encode_read(sequence: u64, deadline_ns: u64) -> [u8; 48] {
    let mut result = [0u8; 48];
    let words = [sequence, deadline_ns, 24, 1, 0, 16];
    for (destination, word) in result.chunks_exact_mut(8).zip(words) {
        destination.copy_from_slice(&word.to_le_bytes());
    }
    result
}

/// Decode the 40-byte successful driver.result and its finite joint position.
pub fn decode_result(frame: &[u8]) -> Option<LowState> {
    let frame = <&[u8; 40]>::try_from(frame).ok()?;
    let word = |offset: usize| u64::from_le_bytes(frame[offset..offset + 8].try_into().unwrap());
    if word(0) != 0 || word(8) != 24 || word(16) != 16 { return None; }
    let tick = u32::try_from(word(24)).ok()?;
    let position = f32::from_bits(u32::try_from(word(32)).ok()?);
    position.is_finite().then_some(LowState { tick, first_joint_position: position })
}
