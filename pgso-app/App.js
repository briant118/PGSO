import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ScrollView,
  Image,
  Linking,
  ActivityIndicator,
  TextInput,
  FlatList,
  Keyboard,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { StatusBar } from 'expo-status-bar';
import { API_BASE_URL } from './config';

function extractResidentId(url) {
  const match = url.match(/\/app\/resident\/(\d+)\/?/);
  return match ? match[1] : null;
}

function HomeScreen({ onScan }) {
  // Simplified home: centered Scan button only
  return (
    <View style={styles.centerContainer}>
      <TouchableOpacity style={styles.btnScan} onPress={onScan}>
        <Text style={styles.btnScanText}>📷 Scan QR Code</Text>
      </TouchableOpacity>
    </View>
  );
}

function ScannerScreen({ onScanned, onBack }) {
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);

  useEffect(() => {
    if (permission === null) {
      requestPermission();
    }
  }, [permission, requestPermission]);

  const handleBarCodeScanned = ({ data }) => {
    if (scanned) return;
    const id = extractResidentId(data);
    if (id) {
      setScanned(true);
      onScanned(id);
    }
  };

  if (!permission) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#17a2b8" />
        <Text style={styles.permissionText}>Requesting camera access...</Text>
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.permissionText}>Camera permission is required to scan QR codes.</Text>
        <TouchableOpacity style={styles.btnPrimary} onPress={requestPermission}>
          <Text style={styles.btnText}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.cameraContainer}>
      <CameraView
        style={StyleSheet.absoluteFillObject}
        facing="back"
        barcodeScannerSettings={{
          barcodeTypes: ['qr'],
        }}
        onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
      />
      {onBack && (
        <TouchableOpacity style={styles.backBtn} onPress={onBack}>
          <Text style={styles.backBtnText}>← Back</Text>
        </TouchableOpacity>
      )}
      <View style={styles.scanOverlay}>
        <View style={styles.scanFrame} />
        <Text style={styles.scanHint}>Point camera at resident QR code</Text>
      </View>
    </View>
  );
}

function ProfileScreen({ residentId, onScanAgain }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/app/api/resident/${residentId}/`)
      .then((res) => {
        if (!res.ok) {
          if (res.status === 404) throw new Error('Resident not found.');
          throw new Error(`Server error (${res.status}). Check that the server is running.`);
        }
        return res.json();
      })
      .then(setData)
      .catch((err) => {
        const msg = (err && err.message) || 'Failed to load resident data';
        const isNetwork = /network|fetch|connection|refused|timeout/i.test(msg);
        setError(isNetwork ? 'Cannot reach server. Ensure phone is on same WiFi, API_BASE_URL in config.js matches your PC IP, and runserver-network.bat is running.' : msg);
      })
      .finally(() => setLoading(false));
  }, [residentId]);

  const handleDownload = () => {
    if (data?.pdf_url) {
      Linking.openURL(data.pdf_url);
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#17a2b8" />
        <Text style={styles.loadingText}>Loading profile...</Text>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>{error || 'Resident not found'}</Text>
        <Text style={styles.hintText}>Ensure your phone is on the same WiFi as the server.</Text>
        <TouchableOpacity style={styles.btnPrimary} onPress={onScanAgain}>
          <Text style={styles.btnText}>Back to Search</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const rows = [
    ['Contact', data.contact_no],
    ['Gender', data.gender],
    ['Status', data.status],
    ['Date of Birth', data.date_of_birth],
    ['Age', `${data.age} years old`],
    ['Place of Birth', data.place_of_birth],
    ['Address', [data.address, data.purok].filter(Boolean).join(' / ')],
    ['Barangay', data.barangay],
    ['Civil Status', data.civil_status],
    ['Occupation', data.occupation],
    ['Educ. Attainment', data.educational_attainment],
    ['Health Status', data.health_status],
    ['Economic Status', data.economic_status],
  ];
  if (data.remarks) rows.push(['Remarks', data.remarks]);

  return (
    <ScrollView style={styles.profileScroll} contentContainerStyle={styles.profileContent}>
      <View style={styles.profileCard}>
        <View style={styles.profileHeader}>
          {data.profile_picture ? (
            <Image source={{ uri: data.profile_picture }} style={styles.avatar} resizeMode="cover" />
          ) : (
            <View style={styles.avatarPlaceholder}>
              <Text style={styles.avatarIcon}>👤</Text>
            </View>
          )}
          <Text style={styles.profileName}>{data.full_name}</Text>
          <Text style={styles.profileId}>ID: {data.resident_id || data.id}</Text>
        </View>
        <View style={styles.profileBody}>
          {rows.map(([label, value]) => (
            <View key={label} style={styles.profileRow}>
              <Text style={styles.profileLabel}>{label}</Text>
              <Text style={styles.profileValue}>{value || '—'}</Text>
            </View>
          ))}
        </View>
        <View style={styles.profileActions}>
          <TouchableOpacity style={styles.btnDownload} onPress={handleDownload}>
            <Text style={styles.btnText}>📥 Download PDF</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.btnSecondary} onPress={onScanAgain}>
            <Text style={styles.btnSecondaryText}>Back to Search</Text>
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );
}

export default function App() {
  const [screen, setScreen] = useState('home');
  const [residentId, setResidentId] = useState(null);

  const handleScanned = (id) => {
    setResidentId(id);
    setScreen('profile');
  };

  const handleSearchSelect = (id) => {
    setResidentId(id);
    setScreen('profile');
  };

  const handleScanAgain = () => {
    setResidentId(null);
    setScreen('home');
  };

  const handleGoToScan = () => {
    setScreen('scanner');
  };

  const handleBackFromScanner = () => {
    setScreen('home');
  };

  const getSubtitle = () => {
    if (screen === 'home') return 'Scan a resident QR code';
    if (screen === 'scanner') return 'Scan a resident QR code';
    return 'Resident Profile';
  };

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      <View style={styles.header}>
        <Text style={styles.headerTitle}>PPS Palawan Profiling System</Text>
        <Text style={styles.headerSubtitle}>{getSubtitle()}</Text>
      </View>
      {screen === 'home' && (
        <HomeScreen
          onScan={handleGoToScan}
        />
      )}
      {screen === 'scanner' && (
        <ScannerScreen
          onScanned={handleScanned}
          onBack={handleBackFromScanner}
        />
      )}
      {screen === 'profile' && (
        <ProfileScreen residentId={residentId} onScanAgain={handleScanAgain} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0d1117',
  },
  header: {
    backgroundColor: '#1e3a5f',
    paddingTop: 48,
    paddingBottom: 16,
    paddingHorizontal: 20,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.9)',
    marginTop: 4,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  permissionText: {
    color: '#8b949e',
    fontSize: 16,
    textAlign: 'center',
    marginTop: 16,
  },
  loadingText: {
    color: '#8b949e',
    marginTop: 12,
  },
  errorText: {
    color: '#f85149',
    fontSize: 16,
    textAlign: 'center',
  },
  hintText: {
    color: '#8b949e',
    fontSize: 14,
    textAlign: 'center',
    marginTop: 8,
  },
  cameraContainer: {
    flex: 1,
  },
  scanOverlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanFrame: {
    width: 250,
    height: 250,
    borderWidth: 2,
    borderColor: 'rgba(23, 162, 184, 0.8)',
    borderRadius: 12,
  },
  scanHint: {
    color: '#fff',
    fontSize: 14,
    marginTop: 24,
    textShadowColor: 'rgba(0,0,0,0.8)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 4,
  },
  btnPrimary: {
    backgroundColor: '#17a2b8',
    paddingVertical: 14,
    paddingHorizontal: 28,
    borderRadius: 12,
    marginTop: 24,
  },
  btnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  profileScroll: {
    flex: 1,
  },
  profileContent: {
    padding: 16,
    paddingBottom: 32,
  },
  profileCard: {
    backgroundColor: '#21262d',
    borderRadius: 16,
    overflow: 'hidden',
  },
  profileHeader: {
    backgroundColor: '#17a2b8',
    padding: 24,
    alignItems: 'center',
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginBottom: 12,
  },
  avatarPlaceholder: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  avatarIcon: {
    fontSize: 36,
  },
  profileName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
    textAlign: 'center',
  },
  profileId: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.9)',
    marginTop: 4,
  },
  profileBody: {
    padding: 16,
  },
  profileRow: {
    flexDirection: 'row',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#30363d',
  },
  profileLabel: {
    width: '38%',
    color: '#8b949e',
    fontSize: 14,
  },
  profileValue: {
    flex: 1,
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  profileActions: {
    padding: 16,
  },
  btnDownload: {
    backgroundColor: '#28a745',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  btnSecondary: {
    backgroundColor: '#30363d',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  btnSecondaryText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  homeContainer: {
    flex: 1,
  },
  searchSection: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#161b22',
    borderBottomWidth: 1,
    borderBottomColor: '#30363d',
  },
  searchInput: {
    flex: 1,
    backgroundColor: '#21262d',
    color: '#fff',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    fontSize: 16,
  },
  searchSpinner: {
    marginLeft: 12,
  },
  searchList: {
    flex: 1,
  },
  searchItem: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#21262d',
  },
  searchItemName: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  searchItemMeta: {
    color: '#8b949e',
    fontSize: 13,
    marginTop: 4,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  emptyText: {
    color: '#8b949e',
    fontSize: 16,
  },
  homeActions: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#30363d',
  },
  btnScan: {
    backgroundColor: '#17a2b8',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  btnScanText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  backBtn: {
    position: 'absolute',
    top: 16,
    left: 16,
    zIndex: 10,
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 12,
  },
  backBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
