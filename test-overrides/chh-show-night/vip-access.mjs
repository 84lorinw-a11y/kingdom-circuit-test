// A game-door code, not authentication or protection for hosted files.
export const VIP_ENTRY_CODE='NOT4SALE';
export const matchesVipCode=value=>typeof value==='string'&&value.trim().toUpperCase().replace(/[\s-]/g,'')===VIP_ENTRY_CODE;
