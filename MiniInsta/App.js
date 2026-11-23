import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator, Image, KeyboardAvoidingView, Platform, Pressable,
  RefreshControl, ScrollView, StyleSheet, Text, TextInput, View,
} from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import * as ImagePicker from 'expo-image-picker';
import * as SecureStore from 'expo-secure-store';

import { request } from './api';

const sessionKey = 'mini-insta-session';
const tabs = ['Feed', 'Profile', 'New post'];

function Button({ title, onPress, disabled, secondary }) {
  return (
    <Pressable accessibilityRole="button" disabled={disabled} onPress={onPress}
      style={[styles.button, secondary && styles.secondary, disabled && styles.disabled]}>
      <Text style={[styles.buttonText, secondary && styles.secondaryText]}>{title}</Text>
    </Pressable>
  );
}

function ErrorText({ message }) {
  return message ? <Text accessibilityRole="alert" style={styles.error}>{message}</Text> : null;
}

function Avatar({ profile, large }) {
  return <Image source={{ uri: profile.profile_image_url }}
    accessibilityLabel={profile.display_name + ' profile photo'}
    style={[styles.avatar, large && styles.avatarLarge]} />;
}

function PostCard({ post }) {
  return (
    <View style={styles.card}>
      <View style={styles.author}>
        <Avatar profile={post.profile} />
        <View style={styles.grow}>
          <Text style={styles.name}>{post.profile.display_name}</Text>
          <Text style={styles.muted}>@{post.profile.username}</Text>
        </View>
        <Text style={styles.muted}>{new Date(post.timestamp).toLocaleDateString()}</Text>
      </View>
      {post.photos.filter(photo => photo.image_url).map(photo => (
        <Image key={photo.id} source={{ uri: photo.image_url }} style={styles.photo}
          accessibilityLabel={'Photo by ' + post.profile.display_name} />
      ))}
      {post.caption ? <Text style={styles.caption}>{post.caption}</Text> : null}
    </View>
  );
}

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function submit() {
    if (busy || !username.trim() || !password) return;
    setBusy(true);
    setError('');
    try {
      const session = await request('/login/', { body: { username: username.trim(), password } });
      await onLogin({ token: session.token, profileId: session.profile.id });
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.login}>
      <Text style={styles.brand}>MiniInsta</Text>
      <Text style={styles.heading}>Sign in</Text>
      <TextInput accessibilityLabel="Username" placeholder="Username" autoCapitalize="none"
        autoCorrect={false} autoComplete="username" value={username} onChangeText={setUsername}
        style={styles.input} />
      <TextInput accessibilityLabel="Password" placeholder="Password" secureTextEntry
        autoComplete="current-password" value={password} onChangeText={setPassword}
        onSubmitEditing={submit} style={styles.input} />
      <ErrorText message={error} />
      <Button title={busy ? 'Signing in…' : 'Sign in'} onPress={submit}
        disabled={busy || !username.trim() || !password} />
    </ScrollView>
  );
}

function Timeline({ session, tab, onExpired }) {
  const [posts, setPosts] = useState([]);
  const [profile, setProfile] = useState(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  const isProfile = tab === 'Profile';

  useEffect(() => {
    const controller = new AbortController();
    const options = { token: session.token, signal: controller.signal };
    const path = '/profiles/' + session.profileId + '/';
    setBusy(true);
    setError('');

    async function load() {
      try {
        const [loadedPosts, loadedProfile] = await Promise.all([
          request(path + (isProfile ? 'posts/' : 'feed/'), options),
          isProfile ? request(path, options) : null,
        ]);
        if (controller.signal.aborted) return;
        setPosts(loadedPosts);
        setProfile(loadedProfile);
      } catch (failure) {
        if (controller.signal.aborted) return;
        if (failure.status === 401) onExpired();
        else setError(failure.message);
      } finally {
        if (!controller.signal.aborted) setBusy(false);
      }
    }

    load();
    return () => controller.abort();
  }, [session, isProfile, revision, onExpired]);

  return (
    <ScrollView contentContainerStyle={styles.content} refreshControl={
      <RefreshControl refreshing={busy} onRefresh={() => setRevision(value => value + 1)} />
    }>
      {profile ? (
        <View style={styles.profile}>
          <Avatar profile={profile} large />
          <Text style={styles.heading}>{profile.display_name}</Text>
          <Text style={styles.muted}>@{profile.username}</Text>
          {profile.bio_text ? <Text style={styles.caption}>{profile.bio_text}</Text> : null}
        </View>
      ) : null}
      <Text style={styles.heading}>{isProfile ? 'Your posts' : 'Feed'}</Text>
      <ErrorText message={error} />
      {error ? <Button title="Retry" secondary onPress={() => setRevision(value => value + 1)} /> : null}
      {!busy && !error && posts.length === 0 ? (
        <Text style={styles.muted}>{isProfile ? 'You haven’t posted yet.' : 'There are no posts from people you follow yet.'}</Text>
      ) : null}
      {posts.map(post => <PostCard key={post.id} post={post} />)}
    </ScrollView>
  );
}

function Composer({ token, onPosted, onExpired }) {
  const [caption, setCaption] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [asset, setAsset] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function pickImage() {
    setError('');
    try {
      const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 0.85 });
      if (!result.canceled) {
        setAsset(result.assets[0]);
        setImageUrl('');
      }
    } catch (failure) {
      setError(failure.message);
    }
  }

  async function publish() {
    if (busy) return;
    setBusy(true);
    setError('');
    try {
      let body = { caption: caption.trim() };
      if (asset) {
        body = new FormData();
        body.append('caption', caption.trim());
        body.append('image_file', {
          uri: asset.uri,
          type: asset.mimeType || 'application/octet-stream',
          name: asset.fileName || asset.uri.split('/').pop() || 'photo.jpg',
        });
      } else if (imageUrl.trim()) {
        body.image_url = imageUrl.trim();
      }
      await request('/posts/', { token, body });
      onPosted();
    } catch (failure) {
      if (failure.status === 401) onExpired();
      else setError(failure.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.content}>
      <Text style={styles.heading}>New post</Text>
      <TextInput accessibilityLabel="Caption" placeholder="Write a caption…" multiline value={caption}
        onChangeText={setCaption} style={[styles.input, styles.multiline]} editable={!busy} />
      {asset ? (
        <>
          <Image source={{ uri: asset.uri }} accessibilityLabel="Selected photo" style={styles.photo} />
          <Button title="Remove photo" secondary disabled={busy} onPress={() => setAsset(null)} />
        </>
      ) : (
        <TextInput accessibilityLabel="Image URL" placeholder="Image URL (optional)" value={imageUrl}
          autoCapitalize="none" keyboardType="url" onChangeText={setImageUrl} style={styles.input}
          editable={!busy} />
      )}
      <Button title="Choose a photo" secondary disabled={busy} onPress={pickImage} />
      <ErrorText message={error} />
      <Button title={busy ? 'Publishing…' : 'Publish'} onPress={publish}
        disabled={busy || !(caption.trim() || imageUrl.trim() || asset)} />
    </ScrollView>
  );
}

export default function App() {
  const [session, setSession] = useState(undefined);
  const [tab, setTab] = useState('Feed');
  const [error, setError] = useState('');

  useEffect(() => {
    SecureStore.getItemAsync(sessionKey).then(value => {
      setSession(value ? JSON.parse(value) : null);
    }).catch(failure => {
      setError(failure.message);
      setSession(null);
    });
  }, []);

  async function signIn(nextSession) {
    await SecureStore.setItemAsync(sessionKey, JSON.stringify(nextSession));
    setError('');
    setTab('Feed');
    setSession(nextSession);
  }

  const signOut = useCallback(async () => {
    try {
      await SecureStore.deleteItemAsync(sessionKey);
      setError('');
    } catch (failure) {
      setError(failure.message);
    }
    setSession(null);
  }, []);

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.safe}>
        <KeyboardAvoidingView style={styles.grow} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
          <ErrorText message={error} />
          {session === undefined ? <ActivityIndicator style={styles.grow} /> : session ? (
            <>
              <View style={styles.header}>
                <Text style={styles.brand}>MiniInsta</Text>
                <Button title="Sign out" secondary onPress={signOut} />
              </View>
              <View style={styles.grow}>
                {tab === 'New post' ? <Composer token={session.token} onPosted={() => setTab('Profile')}
                  onExpired={signOut} /> : <Timeline key={tab} session={session} tab={tab} onExpired={signOut} />}
              </View>
              <View style={styles.tabs}>
                {tabs.map(name => (
                  <Pressable key={name} accessibilityRole="tab" accessibilityState={{ selected: name === tab }}
                    style={[styles.tab, name === tab && styles.activeTab]} onPress={() => setTab(name)}>
                    <Text style={name === tab ? styles.secondaryText : styles.muted}>{name}</Text>
                  </Pressable>
                ))}
              </View>
            </>
          ) : <Login onLogin={signIn} />}
        </KeyboardAvoidingView>
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#faf8f6' },
  grow: { flex: 1 },
  login: { flexGrow: 1, justifyContent: 'center', padding: 28, gap: 16 },
  header: { paddingHorizontal: 20, paddingVertical: 12, flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between', backgroundColor: '#fff', borderBottomWidth: 1, borderColor: '#e7dfdb' },
  brand: { color: '#9b3158', fontSize: 28, fontWeight: '800' },
  heading: { color: '#27212a', fontSize: 23, fontWeight: '700' },
  content: { padding: 20, gap: 14 },
  input: { borderWidth: 1, borderColor: '#cfc4c9', backgroundColor: '#fff', borderRadius: 10,
    padding: 13, fontSize: 16, color: '#27212a' },
  multiline: { minHeight: 100, textAlignVertical: 'top' },
  button: { backgroundColor: '#9b3158', paddingHorizontal: 16, paddingVertical: 12, borderRadius: 10,
    alignItems: 'center' },
  buttonText: { color: '#fff', fontSize: 15, fontWeight: '700' },
  secondary: { backgroundColor: '#f5e5ed' },
  secondaryText: { color: '#852747', fontWeight: '700' },
  disabled: { opacity: 0.5 },
  error: { color: '#a41e2d', fontSize: 15 },
  muted: { color: '#655961', fontSize: 14 },
  profile: { alignItems: 'center', gap: 8, paddingVertical: 12 },
  avatar: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#f0e2e9' },
  avatarLarge: { width: 92, height: 92, borderRadius: 46 },
  card: { borderWidth: 1, borderColor: '#e7dfdb', backgroundColor: '#fff', borderRadius: 14, overflow: 'hidden' },
  author: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 12 },
  name: { fontSize: 15, fontWeight: '700', color: '#27212a' },
  photo: { width: '100%', aspectRatio: 1, backgroundColor: '#f0e2e9' },
  caption: { fontSize: 16, color: '#27212a', padding: 12 },
  tabs: { flexDirection: 'row', padding: 8, gap: 6, backgroundColor: '#fff', borderTopWidth: 1, borderColor: '#e7dfdb' },
  tab: { flex: 1, paddingVertical: 12, alignItems: 'center', borderRadius: 10 },
  activeTab: { backgroundColor: '#f5e5ed' },
});

