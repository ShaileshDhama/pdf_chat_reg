// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract RoleManager is AccessControl, ReentrancyGuard {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant LAWYER_ROLE = keccak256("LAWYER_ROLE");
    bytes32 public constant PARALEGAL_ROLE = keccak256("PARALEGAL_ROLE");
    bytes32 public constant CLIENT_ROLE = keccak256("CLIENT_ROLE");

    struct UserProfile {
        string name;
        string organization;
        string licenseNumber;  // For lawyers
        uint256 joinedAt;
        bool isActive;
        string metadataURI;  // IPFS hash for additional metadata
    }

    mapping(address => UserProfile) public profiles;
    mapping(bytes32 => uint256) public roleMemberCount;

    event RoleGranted(
        bytes32 indexed role,
        address indexed account,
        address indexed sender
    );
    
    event RoleRevoked(
        bytes32 indexed role,
        address indexed account,
        address indexed sender
    );
    
    event ProfileUpdated(
        address indexed account,
        string name,
        string organization,
        string licenseNumber,
        string metadataURI
    );
    
    event UserDeactivated(address indexed account);
    event UserReactivated(address indexed account);

    constructor() {
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(ADMIN_ROLE, msg.sender);
        
        roleMemberCount[DEFAULT_ADMIN_ROLE] = 1;
        roleMemberCount[ADMIN_ROLE] = 1;
    }

    modifier onlyAdmin() {
        require(
            hasRole(ADMIN_ROLE, msg.sender) || hasRole(DEFAULT_ADMIN_ROLE, msg.sender),
            "Caller is not an admin"
        );
        _;
    }

    modifier activeUser(address account) {
        require(profiles[account].isActive, "User is not active");
        _;
    }

    function grantRole(bytes32 role, address account)
        public
        override
        onlyAdmin
        nonReentrant
    {
        require(account != address(0), "Invalid address");
        require(!hasRole(role, account), "Role already granted");

        _grantRole(role, account);
        roleMemberCount[role] += 1;

        emit RoleGranted(role, account, msg.sender);
    }

    function revokeRole(bytes32 role, address account)
        public
        override
        onlyAdmin
        nonReentrant
    {
        require(account != address(0), "Invalid address");
        require(hasRole(role, account), "Role not granted");
        require(
            role != DEFAULT_ADMIN_ROLE || roleMemberCount[DEFAULT_ADMIN_ROLE] > 1,
            "Cannot remove last admin"
        );

        _revokeRole(role, account);
        roleMemberCount[role] -= 1;

        emit RoleRevoked(role, account, msg.sender);
    }

    function updateProfile(
        string memory name,
        string memory organization,
        string memory licenseNumber,
        string memory metadataURI
    ) external activeUser(msg.sender) nonReentrant {
        require(bytes(name).length > 0, "Name cannot be empty");
        
        UserProfile storage profile = profiles[msg.sender];
        
        if (profile.joinedAt == 0) {
            profile.joinedAt = block.timestamp;
            profile.isActive = true;
        }
        
        profile.name = name;
        profile.organization = organization;
        profile.licenseNumber = licenseNumber;
        profile.metadataURI = metadataURI;

        emit ProfileUpdated(
            msg.sender,
            name,
            organization,
            licenseNumber,
            metadataURI
        );
    }

    function deactivateUser(address account) external onlyAdmin nonReentrant {
        require(account != address(0), "Invalid address");
        require(profiles[account].isActive, "User already inactive");
        
        profiles[account].isActive = false;
        
        emit UserDeactivated(account);
    }

    function reactivateUser(address account) external onlyAdmin nonReentrant {
        require(account != address(0), "Invalid address");
        require(!profiles[account].isActive, "User already active");
        
        profiles[account].isActive = true;
        
        emit UserReactivated(account);
    }

    function getUserProfile(address account)
        external
        view
        returns (
            string memory name,
            string memory organization,
            string memory licenseNumber,
            uint256 joinedAt,
            bool isActive,
            string memory metadataURI,
            bytes32[] memory roles
        )
    {
        UserProfile storage profile = profiles[account];
        
        // Get all possible roles
        bytes32[] memory possibleRoles = new bytes32[](4);
        possibleRoles[0] = ADMIN_ROLE;
        possibleRoles[1] = LAWYER_ROLE;
        possibleRoles[2] = PARALEGAL_ROLE;
        possibleRoles[3] = CLIENT_ROLE;
        
        // Count user's roles
        uint256 roleCount = 0;
        for (uint256 i = 0; i < possibleRoles.length; i++) {
            if (hasRole(possibleRoles[i], account)) {
                roleCount++;
            }
        }
        
        // Create array of user's roles
        roles = new bytes32[](roleCount);
        uint256 j = 0;
        for (uint256 i = 0; i < possibleRoles.length; i++) {
            if (hasRole(possibleRoles[i], account)) {
                roles[j] = possibleRoles[i];
                j++;
            }
        }
        
        return (
            profile.name,
            profile.organization,
            profile.licenseNumber,
            profile.joinedAt,
            profile.isActive,
            profile.metadataURI,
            roles
        );
    }

    function getRoleMemberCount(bytes32 role)
        external
        view
        returns (uint256)
    {
        return roleMemberCount[role];
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
