export default class {
    constructor(Options) {
        this.Constants = {
            maxVariables: 320
        };
        this.opCodeTable = [
            { opCode: 0x01n, argsType: 'IL', template: 'SET @%1 #%2' },
            { opCode: 0x02n, argsType: 'II', template: 'SET @%1 $%2' },
            { opCode: 0x03n, argsType: 'I', template: 'CLR @%1' },
            { opCode: 0x04n, argsType: 'I', template: 'INC @%1' },
            { opCode: 0x05n, argsType: 'I', template: 'DEC @%1' },
            { opCode: 0x06n, argsType: 'II', template: 'ADD @%1 $%2' },
            { opCode: 0x07n, argsType: 'II', template: 'SUB @%1 $%2' },
            { opCode: 0x08n, argsType: 'II', template: 'MUL @%1 $%2' },
            { opCode: 0x09n, argsType: 'II', template: 'DIV @%1 $%2' },
            { opCode: 0x0an, argsType: 'II', template: 'BOR @%1 $%2' },
            { opCode: 0x0bn, argsType: 'II', template: 'AND @%1 $%2' },
            { opCode: 0x0cn, argsType: 'II', template: 'XOR @%1 $%2' },
            { opCode: 0x0dn, argsType: 'I', template: 'NOT @%1' },
            { opCode: 0x0en, argsType: 'II', template: 'SET @%1 $($%2)' },
            { opCode: 0x0fn, argsType: 'III', template: 'SET @%1 $($%2 + $%3)' },
            { opCode: 0x10n, argsType: 'I', template: 'PSH $%1' },
            { opCode: 0x11n, argsType: 'I', template: 'POP @%1' },
            { opCode: 0x12n, argsType: 'J', template: 'JSR :%1' },
            { opCode: 0x13n, argsType: '', template: 'RET' },
            { opCode: 0x14n, argsType: 'II', template: 'SET @($%1) $%2' },
            { opCode: 0x15n, argsType: 'III', template: 'SET @($%1 + $%2) $%3' },
            { opCode: 0x16n, argsType: 'II', template: 'MOD @%1 $%2' },
            { opCode: 0x17n, argsType: 'II', template: 'SHL @%1 $%2' },
            { opCode: 0x18n, argsType: 'II', template: 'SHR @%1 $%2' },
            { opCode: 0x1an, argsType: 'J', template: 'JMP :%1' },
            { opCode: 0x1bn, argsType: 'IB', template: 'BZR $%1 :%2' },
            { opCode: 0x1en, argsType: 'IB', template: 'BNZ $%1 :%2' },
            { opCode: 0x1fn, argsType: 'IIB', template: 'BGT $%1 $%2 :%3' },
            { opCode: 0x20n, argsType: 'IIB', template: 'BLT $%1 $%2 :%3' },
            { opCode: 0x21n, argsType: 'IIB', template: 'BGE $%1 $%2 :%3' },
            { opCode: 0x22n, argsType: 'IIB', template: 'BLE $%1 $%2 :%3' },
            { opCode: 0x23n, argsType: 'IIB', template: 'BEQ $%1 $%2 :%3' },
            { opCode: 0x24n, argsType: 'IIB', template: 'BNE $%1 $%2 :%3' },
            { opCode: 0x25n, argsType: 'I', template: 'SLP $%1' },
            { opCode: 0x26n, argsType: 'I', template: 'FIZ $%1' },
            { opCode: 0x27n, argsType: 'I', template: 'STZ $%1' },
            { opCode: 0x28n, argsType: '', template: 'FIN' },
            { opCode: 0x29n, argsType: '', template: 'STP' },
            { opCode: 0x2bn, argsType: 'J', template: 'ERR :%1' },
            { opCode: 0x30n, argsType: '', template: 'PCS' },
            { opCode: 0x32n, argsType: 'F', template: 'FUN %1' },
            { opCode: 0x33n, argsType: 'FI', template: 'FUN %1 $%2' },
            { opCode: 0x34n, argsType: 'FII', template: 'FUN %1 $%2 $%3' },
            { opCode: 0x35n, argsType: 'FI', template: 'FUN @%2 %1' },
            { opCode: 0x36n, argsType: 'FII', template: 'FUN @%2 %1 $%3' },
            { opCode: 0x37n, argsType: 'FIII', template: 'FUN @%2 %1 $%3 $%4' },
            { opCode: 0x7fn, argsType: '', template: 'NOP' }
        ];
        this.apiCodeTable = [
            { apiCode: 0x0100n, opCode: 0x35n, name: 'get_A1' },
            { apiCode: 0x0101n, opCode: 0x35n, name: 'get_A2' },
            { apiCode: 0x0102n, opCode: 0x35n, name: 'get_A3' },
            { apiCode: 0x0103n, opCode: 0x35n, name: 'get_A4' },
            { apiCode: 0x0104n, opCode: 0x35n, name: 'get_B1' },
            { apiCode: 0x0105n, opCode: 0x35n, name: 'get_B2' },
            { apiCode: 0x0106n, opCode: 0x35n, name: 'get_B3' },
            { apiCode: 0x0107n, opCode: 0x35n, name: 'get_B4' },
            { apiCode: 0x0110n, opCode: 0x33n, name: 'set_A1' },
            { apiCode: 0x0111n, opCode: 0x33n, name: 'set_A2' },
            { apiCode: 0x0112n, opCode: 0x33n, name: 'set_A3' },
            { apiCode: 0x0113n, opCode: 0x33n, name: 'set_A4' },
            { apiCode: 0x0114n, opCode: 0x34n, name: 'set_A1_A2' },
            { apiCode: 0x0115n, opCode: 0x34n, name: 'set_A3_A4' },
            { apiCode: 0x0116n, opCode: 0x33n, name: 'set_B1' },
            { apiCode: 0x0117n, opCode: 0x33n, name: 'set_B2' },
            { apiCode: 0x0118n, opCode: 0x33n, name: 'set_B3' },
            { apiCode: 0x0119n, opCode: 0x33n, name: 'set_B4' },
            { apiCode: 0x011an, opCode: 0x34n, name: 'set_B1_B2' },
            { apiCode: 0x011bn, opCode: 0x34n, name: 'set_B3_B4' },
            { apiCode: 0x0120n, opCode: 0x32n, name: 'clear_A' },
            { apiCode: 0x0121n, opCode: 0x32n, name: 'clear_B' },
            { apiCode: 0x0122n, opCode: 0x32n, name: 'clear_A_B' },
            { apiCode: 0x0123n, opCode: 0x32n, name: 'copy_A_From_B' },
            { apiCode: 0x0124n, opCode: 0x32n, name: 'copy_B_From_A' },
            { apiCode: 0x0125n, opCode: 0x35n, name: 'check_A_Is_Zero' },
            { apiCode: 0x0126n, opCode: 0x35n, name: 'check_B_Is_Zero' },
            { apiCode: 0x0127n, opCode: 0x35n, name: 'check_A_equals_B' },
            { apiCode: 0x0128n, opCode: 0x32n, name: 'swap_A_and_B' },
            { apiCode: 0x0129n, opCode: 0x32n, name: 'OR_A_with_B' },
            { apiCode: 0x012an, opCode: 0x32n, name: 'OR_B_with_A' },
            { apiCode: 0x012bn, opCode: 0x32n, name: 'AND_A_with_B' },
            { apiCode: 0x012cn, opCode: 0x32n, name: 'AND_B_with_A' },
            { apiCode: 0x012dn, opCode: 0x32n, name: 'XOR_A_with_B' },
            { apiCode: 0x012en, opCode: 0x32n, name: 'XOR_B_with_A' },
            { apiCode: 0x0140n, opCode: 0x32n, name: 'add_A_to_B' },
            { apiCode: 0x0141n, opCode: 0x32n, name: 'add_B_to_A' },
            { apiCode: 0x0142n, opCode: 0x32n, name: 'sub_A_from_B' },
            { apiCode: 0x0143n, opCode: 0x32n, name: 'sub_B_from_A' },
            { apiCode: 0x0144n, opCode: 0x32n, name: 'mul_A_by_B' },
            { apiCode: 0x0145n, opCode: 0x32n, name: 'mul_B_by_A' },
            { apiCode: 0x0146n, opCode: 0x32n, name: 'div_A_by_B' },
            { apiCode: 0x0147n, opCode: 0x32n, name: 'div_B_by_A' },
            { apiCode: 0x0200n, opCode: 0x32n, name: 'MD5_A_to_B' },
            { apiCode: 0x0201n, opCode: 0x35n, name: 'check_MD5_A_with_B' },
            { apiCode: 0x0202n, opCode: 0x32n, name: 'HASH160_A_to_B' },
            { apiCode: 0x0203n, opCode: 0x35n, name: 'check_HASH160_A_with_B' },
            { apiCode: 0x0204n, opCode: 0x32n, name: 'SHA256_A_to_B' },
            { apiCode: 0x0205n, opCode: 0x35n, name: 'check_SHA256_A_with_B' },
            { apiCode: 0x0300n, opCode: 0x35n, name: 'get_Block_Timestamp' },
            { apiCode: 0x0301n, opCode: 0x35n, name: 'get_Creation_Timestamp' },
            { apiCode: 0x0302n, opCode: 0x35n, name: 'get_Last_Block_Timestamp' },
            { apiCode: 0x0303n, opCode: 0x32n, name: 'put_Last_Block_Hash_In_A' },
            { apiCode: 0x0304n, opCode: 0x33n, name: 'A_to_Tx_after_Timestamp' },
            { apiCode: 0x0305n, opCode: 0x35n, name: 'get_Type_for_Tx_in_A' },
            { apiCode: 0x0306n, opCode: 0x35n, name: 'get_Amount_for_Tx_in_A' },
            { apiCode: 0x0307n, opCode: 0x35n, name: 'get_Timestamp_for_Tx_in_A' },
            { apiCode: 0x0308n, opCode: 0x35n, name: 'get_Ticket_Id_for_Tx_in_A' },
            { apiCode: 0x0309n, opCode: 0x32n, name: 'message_from_Tx_in_A_to_B' },
            { apiCode: 0x030an, opCode: 0x32n, name: 'B_to_Address_of_Tx_in_A' },
            { apiCode: 0x030bn, opCode: 0x32n, name: 'B_to_Address_of_Creator' },
            { apiCode: 0x0400n, opCode: 0x35n, name: 'get_Current_Balance' },
            { apiCode: 0x0401n, opCode: 0x35n, name: 'get_Previous_Balance' },
            { apiCode: 0x0402n, opCode: 0x33n, name: 'send_to_Address_in_B' },
            { apiCode: 0x0403n, opCode: 0x32n, name: 'send_All_to_Address_in_B' },
            { apiCode: 0x0404n, opCode: 0x32n, name: 'send_Old_to_Address_in_B' },
            { apiCode: 0x0405n, opCode: 0x32n, name: 'send_A_to_Address_in_B' },
            { apiCode: 0x0406n, opCode: 0x37n, name: 'add_Minutes_to_Timestamp' }
        ];
        this.programName = '';
        this.programDescription = '';
        this.machineData = '';
        this.instructionSet = [];
        this.version = -1;
        this.reserved = -1;
        this.codePages = -1;
        this.dataPages = -1;
        this.codeStackPages = -1;
        this.userStackPages = -1;
        this.activationAmount = -1n;
        this.attachmentBytes = Options.attachmentBytes ?? '';
        this.creationBytes = Options.creationBytes ?? '';
        this.machineCode = Options.machineCode ?? '';
        this.variables = Options.variables ?? [];
        this.labels = Options.labels ?? [];
        this.padInstruction = Options.padInstruction ?? '';
    }
    /** Triggers the decompilation process
     * @returns Object with properties:
     *  - assemblyProgram: string with the decompiled assembly code
     *  - variables: array with all variables names
     *  - labels: array of Label objects
     * @throws Error if the process fail
     */
    decompile() {
        if (this.attachmentBytes !== '') {
            this.parseAttachmentBytes();
        }
        if (this.creationBytes !== '') {
            this.parseCreationBytes();
        }
        if (this.machineCode.length < 2 && this.creationBytes.length === 0) {
            throw new Error('At least one of byteCodeHexString and attachmentBytes must be supplied.');
        }
        this.decompileByteCode();
        this.addAssemblyLine();
        this.addLabels();
        const programInfo = this.parseProgramInfo();
        const constVariables = this.parseMachineData();
        const variablesDeclaration = this.variables.map(varname => `^declare ${varname}`);
        const instructionList = this.instructionSet.map((Obj) => {
            let retString = '';
            if (Obj.instruction[0] === 0x30n) {
                retString += '\n';
            }
            retString += Obj.label.reduce(this.reduceLabels, '');
            retString += Obj.assemblyline;
            return retString;
        });
        let assemblyProgram = '';
        if (programInfo.length !== 0) {
            assemblyProgram += programInfo.join('\n') + '\n\n';
        }
        if (variablesDeclaration.length !== 0) {
            assemblyProgram += variablesDeclaration.join('\n') + '\n\n';
        }
        if (constVariables.length !== 0) {
            assemblyProgram += constVariables.join('\n') + '\n\n';
        }
        if (instructionList.length === 0) {
            assemblyProgram += '^comment This is a carbon copy contract. Decompile original deployment to get the code.';
        }
        else {
            assemblyProgram += instructionList.join('\n');
        }
        assemblyProgram += '\n';
        this.labels.sort((a, b) => {
            return a.address - b.address;
        });
        return {
            assemblyProgram,
            variables: this.variables,
            labels: this.labels
        };
    }
    reduceLabels(previous, currLabel) {
        if (currLabel.startsWith('fun') || currLabel.startsWith('__fn')) {
            return '\n' + currLabel + ':\n' + previous;
        }
        return currLabel + ':\n' + previous;
    }
    getBytes(input, start, size) {
        let retVal = 0n;
        start *= 2;
        for (let i = 0, multiplier = 1n; i < size; i++, start += 2) {
            const byteStr = input.slice(start, start + 2);
            if (byteStr.length !== 2) {
                throw new Error('Unexpected end of input');
            }
            if (!/^[0-9a-fA-F]+$/.test(byteStr)) {
                throw new Error('Invalid hex string');
            }
            const byte = BigInt('0x' + byteStr);
            retVal += multiplier * byte;
            multiplier *= 256n;
        }
        return retVal;
    }
    parseProgramInfo() {
        const retVal = [];
        if (this.programName !== '') {
            retVal.push(`^program name ${this.programName}`);
        }
        if (this.programDescription !== '') {
            retVal.push(`^program description ${this.programDescription}`);
        }
        if (this.activationAmount !== -1n) {
            retVal.push(`^program activationAmount ${this.activationAmount}`);
        }
        if (this.codeStackPages > 1) {
            retVal.push(`^program codeStackPages ${this.codeStackPages}`);
        }
        if (this.userStackPages > 1) {
            retVal.push(`^program userStackPages ${this.userStackPages}`);
        }
        return retVal;
    }
    parseMachineData() {
        let counter = 0;
        const retVal = [];
        while (counter < this.machineData.length / 2) {
            const value = this.getBytes(this.machineData, counter, 8);
            if (value !== 0n) {
                retVal.push(`^const SET @${this.getMapMemoryName(counter / 8)} #${value.toString(16).padStart(16, '0')}`);
            }
            counter += 8;
        }
        return retVal;
    }
    parseCreationBytes() {
        let counter = 0;
        let bytesToRead;
        for (const prop of ['version', 'reserved', 'codePages', 'dataPages', 'codeStackPages', 'userStackPages']) {
            this[prop] = Number(this.getBytes(this.creationBytes, counter, 2));
            counter += 2;
        }
        this.activationAmount = this.getBytes(this.creationBytes, counter, 8);
        counter += 8;
        bytesToRead = 2;
        if (this.codePages < 2) {
            bytesToRead = 1;
        }
        let codePageLength = Number(this.getBytes(this.creationBytes, counter, bytesToRead));
        counter += bytesToRead;
        if (this.codePages === 1 && codePageLength === 0) {
            codePageLength = 256;
        }
        this.machineCode = this.creationBytes.slice(counter * 2, (counter + codePageLength) * 2);
        counter += codePageLength;
        if (this.machineCode.length !== codePageLength * 2) {
            throw new Error('Invalid attachment machineCode');
        }
        bytesToRead = 2;
        if (this.dataPages < 2) {
            bytesToRead = 1;
        }
        let dataPageLength = Number(this.getBytes(this.creationBytes, counter, bytesToRead));
        counter += bytesToRead;
        if (this.dataPages === 1 && dataPageLength === 0 && (this.creationBytes.length - counter * 2) === 512) {
            dataPageLength = 256;
        }
        this.machineData = this.creationBytes.slice(counter * 2, (counter + dataPageLength) * 2);
        counter += dataPageLength;
        if (this.machineData.length !== dataPageLength * 2) {
            throw new Error('Invalid attachment machineData');
        }
        if (this.creationBytes.length !== counter * 2) {
            throw new Error('Invalid attachmentBytes');
        }
    }
    parseAttachmentBytes() {
        let counter = 0;
        if (this.attachmentBytes.slice(0, 2) !== '01') {
            throw new Error('Invalid attachment type');
        }
        counter++;
        const nameLength = Number(this.getBytes(this.attachmentBytes, counter, 1));
        counter += 1;
        this.programName = this.hexstring2string(this.attachmentBytes.slice(counter * 2, (counter + nameLength) * 2));
        counter += nameLength;
        const descriptionLength = Number(this.getBytes(this.attachmentBytes, counter, 2));
        counter += 2;
        this.programDescription = this.hexstring2string(this.attachmentBytes.slice(counter * 2, (counter + descriptionLength) * 2));
        counter += descriptionLength;
        this.creationBytes = this.attachmentBytes.slice(counter * 2);
    }
    decompileByteCode() {
        let pc = 0; // program counter in chars
        while (pc < this.machineCode.length / 2) {
            const node = {
                ruleIndex: -1,
                address: pc,
                label: [],
                instruction: [],
                assemblyline: ''
            };
            node.instruction.push(this.getBytes(this.machineCode, pc, 1));
            pc++;
            if (node.instruction[0] === 0n) {
                // Allow 00 for padding.
                continue;
            }
            node.ruleIndex = this.opCodeTable.findIndex(obj => obj.opCode === node.instruction[0]);
            if (node.ruleIndex === -1) {
                throw new Error('Found invalid OpCode');
            }
            const foundOpCode = this.opCodeTable[node.ruleIndex];
            for (let i = 0; i < foundOpCode.argsType.length; i++) {
                switch (foundOpCode.argsType.charAt(i)) {
                    case 'I': // variable (integer)
                        node.instruction.push(this.getBytes(this.machineCode, pc, 4));
                        pc += 4;
                        continue;
                    case 'L': // long value
                        node.instruction.push(this.getBytes(this.machineCode, pc, 8));
                        pc += 8;
                        continue;
                    case 'B': // branch offset (byte)
                        node.instruction.push(this.getBytes(this.machineCode, pc, 1));
                        pc++;
                        continue;
                    case 'J': // jump (integer)
                        node.instruction.push(this.getBytes(this.machineCode, pc, 4));
                        pc += 4;
                        continue;
                    case 'F': // API function (short)
                        node.instruction.push(this.getBytes(this.machineCode, pc, 2));
                        pc += 2;
                        continue;
                    default:
                        throw new Error('Internal error');
                }
            }
            this.instructionSet.push(node);
        }
    }
    getMapMemoryName(location) {
        if (location > this.Constants.maxVariables) {
            throw new Error('Bytecode error: Variable outside memory limits');
        }
        if (location >= this.variables.length) {
            for (let idx = this.variables.length; idx <= location; idx++) {
                this.variables.push('var' + idx.toString().padStart(2, '0'));
            }
        }
        return this.variables[location];
    }
    getMapLabelName(address, isJSR) {
        const foundLabel = this.labels.find(obj => obj.address === address);
        if (foundLabel === undefined) {
            const addressLine = this.instructionSet.findIndex(Obj => Obj.address === address);
            if (addressLine === -1) {
                throw new Error('Jump to unknow location');
            }
            let lab = 'lab_';
            if (isJSR) {
                lab = 'function_';
            }
            lab += addressLine.toString(10);
            this.labels.push({ address: address, label: lab });
            return lab;
        }
        return foundLabel.label;
    }
    addAssemblyLine() {
        this.instructionSet.forEach((CurrOp, i) => {
            const foundOpCode = this.opCodeTable[CurrOp.ruleIndex];
            CurrOp.assemblyline = this.padInstruction + foundOpCode.template;
            for (let j = 1; j <= foundOpCode.argsType.length; j++) {
                let foundApi;
                switch (foundOpCode.argsType.charAt(j - 1)) {
                    case 'I': // variable (integer)
                        CurrOp.assemblyline = CurrOp.assemblyline.replace(`%${j}`, this.getMapMemoryName(Number(CurrOp.instruction[j])));
                        continue;
                    case 'L': // long value
                        CurrOp.assemblyline = CurrOp.assemblyline.replace(`%${j}`, CurrOp.instruction[j].toString(16).padStart(16, '0'));
                        continue;
                    case 'B': // branch offset (signed byte)
                        if (CurrOp.instruction[j] > 0x7f) {
                            CurrOp.instruction[j] += -256n;
                        }
                        CurrOp.assemblyline = CurrOp.assemblyline.replace(`%${j}`, this.getMapLabelName(CurrOp.address + Number(CurrOp.instruction[j]), false));
                        continue;
                    case 'J': // jump (integer)
                        if (foundOpCode.opCode === 0x12n) {
                            CurrOp.assemblyline = CurrOp.assemblyline.replace(`%${j}`, this.getMapLabelName(Number(CurrOp.instruction[j]), true));
                            continue;
                        }
                        CurrOp.assemblyline = CurrOp.assemblyline.replace(`%${j}`, this.getMapLabelName(Number(CurrOp.instruction[j]), false));
                        continue;
                    case 'F': // API function (short)
                        foundApi = this.apiCodeTable.find(obj => obj.apiCode === CurrOp.instruction[j] && obj.opCode === CurrOp.instruction[0]);
                        if (foundApi === undefined) {
                            throw new Error('Found invalid api function code');
                        }
                        CurrOp.assemblyline = CurrOp.assemblyline.replace(`%${j}`, foundApi.name);
                        continue;
                    default:
                        throw new Error('Internal error');
                }
            }
        });
    }
    addLabels() {
        this.labels.forEach((LabelObj) => {
            const foundInstruction = this.instructionSet.find(obj => obj.address === LabelObj.address);
            if (foundInstruction === undefined) {
                throw new Error('Invalid label object was suplied');
            }
            foundInstruction.label.push(LabelObj.label);
        });
    }
    hexstring2string(inHexStr) {
        let c1, c2, c3, c4, cc;
        let i = 0;
        let ret = '';
        do {
            if (i >= inHexStr.length) {
                return ret;
            }
            c1 = parseInt(inHexStr.slice(i, i + 2), 16);
            i += 2;
            if (c1 < 128) {
                if (c1 >= 32) {
                    ret += String.fromCharCode(c1);
                }
                continue;
            }
            if ((c1 & 0xE0) === 0xC0) { // twobytes utf8
                if (i >= inHexStr.length) {
                    return ret;
                }
                c2 = parseInt(inHexStr.slice(i, i + 2), 16);
                i += 2;
                if ((c2 & 0xC0) === 0x80) {
                    ret += String.fromCharCode((c2 & 0x3F) | ((c1 & 0x1F) << 6));
                }
                continue;
            }
            if ((c1 & 0xF0) === 0xE0) { // threebytes utf8
                if (i + 2 >= inHexStr.length) {
                    return ret;
                }
                c2 = parseInt(inHexStr.slice(i, i + 2), 16);
                i += 2;
                c3 = parseInt(inHexStr.slice(i, i + 2), 16);
                i += 2;
                if (((c2 & 0xC0) === 0x80) && ((c3 & 0xC0) === 0x80)) {
                    ret += String.fromCharCode((c3 & 0x3F) | ((c2 & 0x3F) << 6) | ((c1 & 0xF) << 12));
                }
                continue;
            }
            if ((c1 & 0xF8) === 0xF0) { // fourbytes utf8
                if (i + 4 >= inHexStr.length) {
                    return ret;
                }
                c2 = parseInt(inHexStr.slice(i, i + 2), 16);
                i += 2;
                c3 = parseInt(inHexStr.slice(i, i + 2), 16);
                i += 2;
                c4 = parseInt(inHexStr.slice(i, i + 2), 16);
                i += 2;
                if (((c2 & 0xC0) === 0x80) && ((c3 & 0xC0) === 0x80) && ((c4 & 0xC0) === 0x80)) {
                    cc = (c4 & 0x3F) | ((c3 & 0x3F) << 6) | ((c2 & 0x3F) << 12) | ((c1 & 0x7) << 18);
                    cc -= 0x10000;
                    ret += String.fromCharCode((cc >> 10) | 0xd800) + String.fromCharCode((cc & 0x3FF) | 0xDc00);
                }
                continue;
            }
        } while (true);
    }
}
//# sourceMappingURL=index.js.map