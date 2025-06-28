Okay, I have updated all the JSON examples in the document to use `TransactionType` instead of `transaction_type` and also corrected other key naming inconsistencies (e.g., `account` to `Account`, `signing_pub_key` to `SigningPubKey`, etc.) to ensure consistency with the standard XRPL CamelCase naming convention used throughout the documentation text.

Here is the revised document:

---

# XRPL Transaction Types Documentation

This document provides detailed information about all transaction types available in the XRP Ledger, their required and optional parameters, and the flags that can be used with them.

## Common Transaction Fields

All transactions in the XRP Ledger share the following common fields:

| Field | Required | Description |
|-------|----------|-------------|
| `Account` | Yes | The sender's XRPL address |
| `TransactionType` | Yes | The type of transaction (e.g., "Payment", "AccountSet", etc.) |
| `Fee` | No (Auto-fillable) | The amount of XRP to destroy as a transaction cost (specified in drops) |
| `Sequence` | No (Auto-fillable) | The sequence number of the transaction |
| `LastLedgerSequence` | No (Auto-fillable) | The highest ledger index this transaction can appear in |
| `SourceTag` | No | An arbitrary source tag representing a hosted user or specific purpose |
| `Memos` | No | Additional arbitrary information attached to the transaction |
| `Signers` | No | For multi-signed transactions, signing data authorizing the transaction |

## Critical Format Information

### Amount Formats

XRP Ledger transactions can use two types of currency amounts: XRP and issued currencies.

#### XRP Amount Format
XRP is specified as a string representing the amount in drops (1 XRP = 1,000,000 drops).

Example: `"1000000"` (represents 1 XRP)

#### Issued Currency Amount Format
Issued currencies are specified as objects with three fields:```json
{
  "Currency": "USD",
  "Issuer": "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq",
  "Value": "100"
}
```

- `Currency`: Three-character currency code (or hex code for non-standard currencies)
- `Issuer`: XRPL address of the currency issuer
- `Value`: String representation of the amount

**Important Note**: if currency length is more than 3 the currency should be passed as hex-string . use convert currency tool to convert it. if currency is USD you can pass it directly if currency is USDC you should convert into HEX and pass it.

### Flag Formats

Flags can be specified in three ways:

1.  **Integer format**: A single integer with all the appropriate bits set
    Example: `131072` (represents TF_PARTIAL_PAYMENT)

2.  **Array format**: Array of integers representing individual flags
    Example: `[131072, 65536]` (represents TF_PARTIAL_PAYMENT and TF_NO_RIPPLE_DIRECT)

3.  **Dictionary format**: Object with flag names and boolean values
    Example: `{"TF_PARTIAL_PAYMENT": true, "TF_NO_RIPPLE_DIRECT": false}`

**Important Note**: For AccountSet transactions, the `SetFlag` and `ClearFlag` fields are separate parameters that accept integer values, not part of the `Flags` field.

### Memo Format

Memos are specified as an array of objects:

```json
[
  {
    "Memo": {
      "MemoData": "4861707079204E657720596561722032303234",
      "MemoFormat": "746578742F706C61696E",
      "MemoType": "687474703A2F2F6578616D706C652E636F6D2F6D656D6F2F67656E65726963"
    }
  }
]
```

- `MemoData`: Hex-encoded string containing the content of the memo
- `MemoFormat`: Hex-encoded string indicating the format (usually MIME type)
- `MemoType`: Hex-encoded string indicating the type (usually an RFC 5988 relation)

At least one of these fields must be present in each Memo object.

### Path Format

For cross-currency payments, paths are specified as arrays of arrays of path steps:

```json
[
  [
    {"Account": "rAccount1", "Currency": "USD", "Issuer": "rIssuer1"},
    {"Account": "rAccount2", "Currency": "EUR", "Issuer": "rIssuer2"}
  ],
  [
    {"Account": "rAccount3", "Currency": "GBP", "Issuer": "rIssuer3"},
    {"Account": "rAccount4", "Currency": "EUR", "Issuer": "rIssuer4"}
  ]
]
```

Each path is an array of path steps, and each path step is an object with Account, Currency, and Issuer fields.

## Detailed Transaction Types

### 1. Payment

Sends value from one account to another, either in XRP or issued currencies.

**Required Fields**:
- `Destination`: The address of the account receiving the payment
- `Amount`: The amount to deliver (format varies by currency type)

**Optional Fields**:
- `DestinationTag`: Integer identifying the reason for payment or hosted recipient
- `InvoiceID`: 256-bit hash identifying a specific reason or identifier
- `Paths`: Array of payment paths for cross-currency payments
- `SendMax`: Maximum amount to deduct from sending account (for issued currency payments)
- `DeliverMin`: Minimum amount to deliver (only valid with TF_PARTIAL_PAYMENT flag)

**Available Flags**:
- `TF_NO_RIPPLE_DIRECT (0x00010000)`: Do not use the default path; only use specified paths
- `TF_PARTIAL_PAYMENT (0x00020000)`: Allow payment to send less than full amount
- `TF_LIMIT_QUALITY (0x00040000)`: Only use paths with specified quality or better

**Examples**:

1. Simple XRP Payment:
```json
{
  "TransactionType": "Payment",
  "Account": "rSendingAccount...",
  "Destination": "rDestination...",
  "Amount": "1000000",
}
```

2. Issued Currency Payment:
```json
{
  "TransactionType": "Payment",
  "Account": "rSendingAccount...",
  "Destination": "rDestination...",
  "Amount": {
    "Currency": "USD",
    "Issuer": "rIssuer...",
    "Value": "100"
  }
}
```

3. Partial Payment with Path and Send Max:
```json
{
  "TransactionType": "Payment",
  "Account": "rSendingAccount...",
  "Destination": "rDestination...",
  "Amount": {
    "Currency": "USD",
    "Issuer": "rIssuer1...",
    "Value": "100"
  },
  "SendMax": {
    "Currency": "EUR",
    "Issuer": "rIssuer2...",
    "Value": "120"
  },
  "Paths": [
    [
      {"Account": "rIntermediary1", "Currency": "EUR", "Issuer": "rIssuer2"},
      {"Account": "rIntermediary2", "Currency": "USD", "Issuer": "rIssuer1"}
    ]
  ],
  "Flags": {"TF_PARTIAL_PAYMENT": true},
}
```

### 2. AccountSet

Modifies settings for an XRPL account.

**Optional Fields**:
- `ClearFlag`: Integer value to disable a specific account flag
- `Domain`: Hex representation of a domain associated with this account
- `EmailHash`: Hash of email address for generating avatar image
- `MessageKey`: Public key for sending encrypted messages to this account
- `SetFlag`: Integer value to enable a specific account flag
- `TransferRate`: Fee to charge when users transfer this account's currencies (0-1000 for 0%-1%)
- `TickSize`: Tick size for offers involving currencies issued by this address (0-15)

**Available Flag Values for SetFlag/ClearFlag**:
- `asfAccountTxnID (5)`: Track the ID of this account's most recent transaction
- `asfDefaultRipple (8)`: Enable rippling on trust lines by default
- `asfDepositAuth (9)`: Require deposit authorization
- `asfDisableMaster (4)`: Disallow use of the master key pair
- `asfDisallowXRP (3)`: Disallow sending XRP
- `asfGlobalFreeze (7)`: Freeze all assets issued by this account
- `asfNoFreeze (6)`: Permanently give up the ability to freeze individual trust lines
- `asfRequireAuth (2)`: Require authorization for users to hold this account's issued currencies
- `asfRequireDest (1)`: Require a destination tag for payments

**Examples**:

1. Enable Default Ripple:
```json
{
  "TransactionType": "AccountSet",
  "Account": "rAccount...",
  "SetFlag": 8
}
```

2. Set Domain and Require Destination Tags:
```json
{
  "TransactionType": "AccountSet",
  "Account": "rAccount...",
  "Domain": "6578616D706C652E636F6D", // "example.com" in hex
  "SetFlag": 1
}
```

3. Set Transfer Rate to 0.2%:
```json
{
  "TransactionType": "AccountSet",
  "Account": "rAccount...",
  "TransferRate": 1002000000
}
```
*Note: Corrected TransferRate calculation. 1,000,000,000 means no fee (1.0 multiplier). 1,002,000,000 means 0.2% fee (1.002 multiplier).*

### 3. TrustSet

Creates or modifies a trust line linking two accounts.

**Required Fields**:
- `LimitAmount`: Object defining the currency, issuer, and maximum amount of currency that can be held

**Optional Fields**:
- `QualityIn`: Integer representing the inbound quality (incoming payments)
- `QualityOut`: Integer representing the outbound quality (outgoing payments)

**Available Flags**:
- `TF_CLEAR_FREEZE (0x00200000)`: Clear the freeze on the trust line
- `TF_SET_FREEZE (0x00100000)`: Freeze the trust line
- `TF_SET_NO_RIPPLE (0x00020000)`: Disable rippling through this trust line
- `TF_CLEAR_NO_RIPPLE (0x00040000)`: Enable rippling through this trust line

**Examples**:

1. Create Trust Line for USD:
```json
{
  "TransactionType": "TrustSet",
  "Account": "rAccount...",
  "LimitAmount": {
    "Currency": "USD",
    "Issuer": "rIssuer...",
    "Value": "10000"
  }
}
```

2. Modify Trust Line with No Ripple Flag:
```json
{
  "TransactionType": "TrustSet",
  "Account": "rAccount...",
  "LimitAmount": {
    "Currency": "EUR",
    "Issuer": "rIssuer...",
    "Value": "5000"
  },
  "Flags": {"TF_SET_NO_RIPPLE": true}
}
```

3. Freeze a Trust Line:
```json
{
  "TransactionType": "TrustSet",
  "Account": "rAccount...",
  "LimitAmount": {
    "Currency": "GBP",
    "Issuer": "rIssuer...",
    "Value": "1000"
  },
  "Flags": {"TF_SET_FREEZE": true}
}
```

### 4. OfferCreate

Places an offer in the XRP Ledger's decentralized exchange.

**Required Fields**:
- `TakerGets`: The amount the taker gets (what creator is selling)
- `TakerPays`: The amount the taker pays (what creator is buying)

**Optional Fields**:
- `Expiration`: Time after which the offer is no longer valid (seconds since Ripple Epoch)
- `OfferSequence`: Sequence number of a previous offer to cancel first

**Available Flags**:
- `TF_PASSIVE (0x00010000)`: If enabled, the offer doesn't consume matching offers
- `TF_IMMEDIATE_OR_CANCEL (0x00020000)`: Treat as an immediate-or-cancel order
- `TF_FILL_OR_KILL (0x00040000)`: Treat as a fill-or-kill order
- `TF_SELL (0x00080000)`: Compute amounts from TakerGets perspective

**Examples**:

1. Sell XRP for USD:
```json
{
  "TransactionType": "OfferCreate",
  "Account": "rAccount...",
  "TakerPays": {
    "Currency": "USD",
    "Issuer": "rIssuer...",
    "Value": "100"
  },
  "TakerGets": "150000000"
}
```

2. Buy EUR with USD (Passive):
```json
{
  "TransactionType": "OfferCreate",
  "Account": "rAccount...",
  "TakerPays": {
    "Currency": "EUR",
    "Issuer": "rIssuer1...",
    "Value": "50"
  },
  "TakerGets": {
    "Currency": "USD",
    "Issuer": "rIssuer2...",
    "Value": "60"
  },
  "Flags": {"TF_PASSIVE": true}
}
```

3. Sell Offer with Fill-or-Kill:
```json
{
  "TransactionType": "OfferCreate",
  "Account": "rAccount...",
  "TakerGets": {
    "Currency": "USD",
    "Issuer": "rIssuer...",
    "Value": "100"
  },
  "TakerPays": "120000000", // 120 XRP
  "Flags": {"TF_SELL": true, "TF_FILL_OR_KILL": true},
  "Expiration": 595640108 // Optional: Time when the offer expires
}
```

### 5. OfferCancel

Cancels an existing offer from the XRP Ledger.

**Required Fields**:
- `OfferSequence`: The sequence number of the offer to cancel

**Example**:

```json
{
  "TransactionType": "OfferCancel",
  "Account": "rAccount...",
  "OfferSequence": 123456
}
```

### 6. NFTokenMint

Creates a new non-fungible token.

**Required Fields**:
- `TokenTaxon`: Integer indicating the type of token being minted (0-4294967295)

**Optional Fields**:
- `Issuer`: The account that should be the issuer of the token (defaults to the sending account)
- `TransferFee`: The fee charged by the issuer for secondary sales (0-50000, representing 0% to 50%)
- `URI`: URI pointing to the token's metadata (hex string, max 256 bytes)

**Available Flags**:
- `TF_BURNABLE (0x00000001)`: Allow the token to be burned
- `TF_ONLY_XRP (0x00000002)`: Only allow offers in XRP
- `TF_TRUSTLINE (0x00000004)`: Allow transfer to accounts without trustline
- `TF_TRANSFERABLE (0x00000008)`: Allow the token to be transferred

**Examples**:

1. Basic NFT Mint:
```json
{
  "TransactionType": "NFTokenMint",
  "Account": "rAccount...",
  "TokenTaxon": 0,
  "Flags": {"TF_TRANSFERABLE": true}
}
```

2. NFT with URI and Transfer Fee:
```json
{
  "TransactionType": "NFTokenMint",
  "Account": "rAccount...",
  "TokenTaxon": 1,
  "URI": "697066733A2F2F516D6162637879...", // IPFS URI in hex
  "TransferFee": 5000, // 5%
  "Flags": {"TF_TRANSFERABLE": true, "TF_BURNABLE": true}
}
```

### 7. NFTokenCreateOffer

Creates an offer to buy or sell an NFT.

**Required Fields**:
- `NFTokenID`: The unique identifier of the NFToken
- `Amount`: The amount to pay for the token (XRP or issued currency)

**Optional Fields**:
- `Expiration`: Time after which the offer is no longer valid
- `Destination`: Account the offer is intended for (for direct offers)
- `Owner`: Owner of the NFToken (if the offer is to buy)

**Available Flags**:
- `TF_SELL (0x00000001)`: Offer is to sell an owned NFToken
- `TF_AUTHORIZED (0x00000002)`: Authorize the recipient to mint a copy of this NFToken

**Examples**:

1. Sell Offer for NFT:
```json
{
  "TransactionType": "NFTokenCreateOffer",
  "Account": "rAccount...",
  "NFTokenID": "00081388DC1AB4937C899037B2779C71CDC394F61D6D8C7800E08C12129E1BBB0000000D",
  "Amount": "10000000", // 10 XRP
  "Flags": {"TF_SELL": true}
}
```

2. Buy Offer for NFT with Issued Currency:
```json
{
  "TransactionType": "NFTokenCreateOffer",
  "Account": "rAccount...",
  "NFTokenID": "00081388DC1AB4937C899037B2779C71CDC394F61D6D8C7800E08C12129E1BBB0000000D",
  "Owner": "rOwner...",
  "Amount": {
    "Currency": "USD",
    "Issuer": "rIssuer...",
    "Value": "100"
  },
  "Destination": "rSeller..."
}
```

### Additional Transactions

There are many more transaction types in the XRP Ledger, including:

- **NFTokenAcceptOffer**: Accept a buy or sell offer for an NFT
- **NFTokenCancelOffer**: Cancel existing NFT offers
- **NFTokenBurn**: Destroy an NFT
- **EscrowCreate**: Create a time-locked or condition-based payment
- **EscrowFinish**: Complete an escrow payment
- **EscrowCancel**: Cancel an expired escrow
- **AMMCreate**: Create an Automated Market Maker instance
- **AMMDeposit**: Add liquidity to an AMM
- **AMMWithdraw**: Remove liquidity from an AMM
- **SetRegularKey**: Assign a regular key pair to account
- **SignerListSet**: Add/remove multi-signing capabilities
- **TicketCreate**: Create tickets for sequence numbers
- **DepositPreauth**: Preauthorize an account to send payments

## Using the CREATE_TRANSACTION Tool

When using the CREATE_TRANSACTION tool, you need to provide:

1.  `TransactionType`: The type of transaction as a string (e.g., "Payment", "AccountSet", "TrustSet")
2.  `Account`: The sender's XRPL address
3.  `SigningPubKey`: The public key for signing the transaction
4.  `TransactionParams`: A dictionary containing all transaction-specific parameters
5.  Optional fields like `Flags`, `Fee`, `Sequence`, etc.

### Examples

#### XRP Payment:

```json
{
  "TransactionType": "Payment",
  "Account": "rSenderAccount...",
  "TransactionParams": {
    "Destination": "rDestination...",
    "Amount": "1000000"
  }
}
```

#### Issued Currency Payment with Partial Payment Flag:

```json
{
  "TransactionType": "Payment",
  "Account": "rSenderAccount...",
  "TransactionParams": {
    "Destination": "rDestination...",
    "Amount": {
      "Currency": "USD",
      "Issuer": "rIssuer...",
      "Value": "100"
    },
    "SendMax": {
      "Currency": "USD",
      "Issuer": "rIssuer...",
      "Value": "110"
    }
  },
  "Flags": {"TF_PARTIAL_PAYMENT": true}
}
```

#### AccountSet with Default Ripple:

```json
{
  "TransactionType": "AccountSet",
  "Account": "rAccount...",
  "TransactionParams": {
    "SetFlag": 8
  }
}
```

#### TrustSet for USD:

```json
{
  "TransactionType": "TrustSet",
  "Account": "rAccount...",
  "SigningPubKey": "02F89EAEC7667B30F33D0687BBA86C3FE2A08CCA40A9186C5BDE2DAA6FA97A37DE",
  "TransactionParams": {
    "LimitAmount": {
      "Currency": "USD",
      "Issuer": "rIssuer...",
      "Value": "1000"
    }
  },
  "Flags": {"TF_SET_NO_RIPPLE": true}
}
```

The tool will autofill necessary fields like Fee, Sequence, and LastLedgerSequence based on current network conditions and return the prepared transaction ready for signing and submission.

---

