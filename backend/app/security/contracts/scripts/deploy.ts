import { ethers } from "hardhat";
import { writeFileSync } from "fs";
import { join } from "path";

async function main() {
    const [deployer] = await ethers.getSigners();
    console.log("Deploying contracts with account:", deployer.address);

    // Deploy RoleManager
    console.log("Deploying RoleManager...");
    const RoleManager = await ethers.getContractFactory("RoleManager");
    const roleManager = await RoleManager.deploy();
    await roleManager.deployed();
    console.log("RoleManager deployed to:", roleManager.address);

    // Deploy DocumentRegistry
    console.log("Deploying DocumentRegistry...");
    const DocumentRegistry = await ethers.getContractFactory("DocumentRegistry");
    const documentRegistry = await DocumentRegistry.deploy();
    await documentRegistry.deployed();
    console.log("DocumentRegistry deployed to:", documentRegistry.address);

    // Grant REGISTRAR_ROLE to DocumentRegistry contract
    const registrarRole = ethers.utils.keccak256(
        ethers.utils.toUtf8Bytes("REGISTRAR_ROLE")
    );
    await documentRegistry.grantRole(registrarRole, documentRegistry.address);
    console.log("Granted REGISTRAR_ROLE to DocumentRegistry");

    // Save contract addresses and ABIs
    const contracts = {
        RoleManager: {
            address: roleManager.address,
            abi: JSON.parse(RoleManager.interface.format("json") as string),
        },
        DocumentRegistry: {
            address: documentRegistry.address,
            abi: JSON.parse(DocumentRegistry.interface.format("json") as string),
        },
    };

    // Save to files
    const contractsDir = join(__dirname, "..", "artifacts");
    writeFileSync(
        join(contractsDir, "RoleManager.json"),
        JSON.stringify(contracts.RoleManager, null, 2)
    );
    writeFileSync(
        join(contractsDir, "DocumentRegistry.json"),
        JSON.stringify(contracts.DocumentRegistry, null, 2)
    );
    console.log("Contract artifacts saved to:", contractsDir);

    // Verify contracts on Etherscan
    if (process.env.ETHERSCAN_API_KEY) {
        console.log("Verifying contracts on Etherscan...");
        await hre.run("verify:verify", {
            address: roleManager.address,
            constructorArguments: [],
        });
        await hre.run("verify:verify", {
            address: documentRegistry.address,
            constructorArguments: [],
        });
        console.log("Contracts verified on Etherscan");
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
