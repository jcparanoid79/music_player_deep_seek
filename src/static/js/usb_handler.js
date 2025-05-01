class USBDeviceHandler {
    constructor() {
        this.devices = new Map();
        this.onDeviceChange = null;
    }

    async initialize() {
        navigator.usb.addEventListener('connect', this.handleConnectedDevice.bind(this));
        navigator.usb.addEventListener('disconnect', this.handleDisconnectedDevice.bind(this));
        
        // Get initially connected devices
        const devices = await navigator.usb.getDevices();
        devices.forEach(device => this.handleConnectedDevice({ device }));
    }

    async requestDevice() {
        try {
            const device = await navigator.usb.requestDevice({
                filters: [
                    // Mass storage class
                    { classCode: 0x08 },
                    // MTP class
                    { classCode: 0x06, subclassCode: 0x01 }
                ]
            });
            await this.handleConnectedDevice({ device });
            return device;
        } catch (error) {
            console.error('Error requesting USB device:', error);
            throw error;
        }
    }

    async handleConnectedDevice(event) {
        const device = event.device;
        try {
            await device.open();
            this.devices.set(device.serialNumber, device);
            
            const deviceInfo = {
                id: `usb-${device.vendorId.toString(16)}:${device.productId.toString(16)}`,
                vendorId: device.vendorId,
                productId: device.productId,
                serialNumber: device.serialNumber,
                manufacturerName: device.manufacturerName,
                productName: device.productName
            };

            if (this.onDeviceChange) {
                this.onDeviceChange('connected', deviceInfo);
            }

            // Notify backend
            await this.notifyBackend('connected', deviceInfo);
        } catch (error) {
            console.error('Error handling connected device:', error);
        }
    }

    async handleDisconnectedDevice(event) {
        const device = event.device;
        this.devices.delete(device.serialNumber);

        const deviceInfo = {
            id: `usb-${device.vendorId.toString(16)}:${device.productId.toString(16)}`,
            serialNumber: device.serialNumber
        };

        if (this.onDeviceChange) {
            this.onDeviceChange('disconnected', deviceInfo);
        }

        // Notify backend
        await this.notifyBackend('disconnected', deviceInfo);
    }

    async notifyBackend(event, deviceInfo) {
        try {
            await fetch('/api/devices/notify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    event,
                    device: deviceInfo
                })
            });
        } catch (error) {
            console.error('Error notifying backend:', error);
        }
    }

    setDeviceChangeListener(callback) {
        this.onDeviceChange = callback;
    }
}

// Initialize handler
const usbHandler = new USBDeviceHandler();
usbHandler.initialize().catch(console.error);

// Export for use in other modules
// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = usbHandler;
} else {
    window.usbHandler = usbHandler;
}
