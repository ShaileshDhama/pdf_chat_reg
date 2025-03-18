// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

contract DocumentRegistry is AccessControl, ReentrancyGuard {
    using ECDSA for bytes32;

    bytes32 public constant REGISTRAR_ROLE = keccak256("REGISTRAR_ROLE");
    
    struct Document {
        address owner;
        string ipfsHash;
        uint256 timestamp;
        bytes32 contentHash;
        bool isVerified;
        mapping(address => bool) hasAccess;
        mapping(address => string) encryptedKeys;
    }
    
    // documentHash => Document
    mapping(bytes32 => Document) public documents;
    
    // Tracking document hashes for each user
    mapping(address => bytes32[]) public userDocuments;
    
    event DocumentRegistered(
        bytes32 indexed documentHash,
        address indexed owner,
        string ipfsHash,
        uint256 timestamp
    );
    
    event DocumentVerified(
        bytes32 indexed documentHash,
        address indexed verifier,
        uint256 timestamp
    );
    
    event AccessGranted(
        bytes32 indexed documentHash,
        address indexed grantee,
        uint256 timestamp
    );
    
    event AccessRevoked(
        bytes32 indexed documentHash,
        address indexed grantee,
        uint256 timestamp
    );

    constructor() {
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(REGISTRAR_ROLE, msg.sender);
    }

    function registerDocument(
        bytes32 documentHash,
        string memory ipfsHash,
        bytes32 contentHash,
        string memory encryptedKey
    ) external nonReentrant {
        require(documentHash != bytes32(0), "Invalid document hash");
        require(bytes(ipfsHash).length > 0, "Invalid IPFS hash");
        require(
            documents[documentHash].timestamp == 0,
            "Document already registered"
        );

        Document storage doc = documents[documentHash];
        doc.owner = msg.sender;
        doc.ipfsHash = ipfsHash;
        doc.timestamp = block.timestamp;
        doc.contentHash = contentHash;
        doc.isVerified = false;
        doc.hasAccess[msg.sender] = true;
        doc.encryptedKeys[msg.sender] = encryptedKey;

        userDocuments[msg.sender].push(documentHash);

        emit DocumentRegistered(
            documentHash,
            msg.sender,
            ipfsHash,
            block.timestamp
        );
    }

    function verifyDocument(bytes32 documentHash)
        external
        onlyRole(REGISTRAR_ROLE)
    {
        require(
            documents[documentHash].timestamp > 0,
            "Document not registered"
        );
        require(
            !documents[documentHash].isVerified,
            "Document already verified"
        );

        documents[documentHash].isVerified = true;

        emit DocumentVerified(documentHash, msg.sender, block.timestamp);
    }

    function grantAccess(
        bytes32 documentHash,
        address grantee,
        string memory encryptedKey
    ) external {
        require(
            documents[documentHash].timestamp > 0,
            "Document not registered"
        );
        require(
            documents[documentHash].owner == msg.sender,
            "Not document owner"
        );
        require(
            !documents[documentHash].hasAccess[grantee],
            "Already has access"
        );

        documents[documentHash].hasAccess[grantee] = true;
        documents[documentHash].encryptedKeys[grantee] = encryptedKey;

        emit AccessGranted(documentHash, grantee, block.timestamp);
    }

    function revokeAccess(bytes32 documentHash, address grantee) external {
        require(
            documents[documentHash].timestamp > 0,
            "Document not registered"
        );
        require(
            documents[documentHash].owner == msg.sender,
            "Not document owner"
        );
        require(
            documents[documentHash].hasAccess[grantee],
            "Does not have access"
        );
        require(grantee != msg.sender, "Cannot revoke own access");

        documents[documentHash].hasAccess[grantee] = false;
        delete documents[documentHash].encryptedKeys[grantee];

        emit AccessRevoked(documentHash, grantee, block.timestamp);
    }

    function getDocument(bytes32 documentHash)
        external
        view
        returns (
            address owner,
            string memory ipfsHash,
            uint256 timestamp,
            bytes32 contentHash,
            bool isVerified,
            bool hasAccess,
            string memory encryptedKey
        )
    {
        Document storage doc = documents[documentHash];
        require(doc.timestamp > 0, "Document not registered");
        require(
            doc.hasAccess[msg.sender],
            "No access to document"
        );

        return (
            doc.owner,
            doc.ipfsHash,
            doc.timestamp,
            doc.contentHash,
            doc.isVerified,
            doc.hasAccess[msg.sender],
            doc.encryptedKeys[msg.sender]
        );
    }

    function getUserDocuments(address user)
        external
        view
        returns (bytes32[] memory)
    {
        return userDocuments[user];
    }

    function hasDocumentAccess(bytes32 documentHash, address user)
        external
        view
        returns (bool)
    {
        return documents[documentHash].hasAccess[user];
    }
}
