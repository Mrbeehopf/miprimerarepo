import 'dart:convert';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_web_auth_2/flutter_web_auth_2.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/spotify_track.dart';

class SpotifyService {
  static const _tokenKey = 'spotify_access_token';
  static const _tokenExpiryKey = 'spotify_token_expiry';

  String get _clientId => dotenv.env['SPOTIFY_CLIENT_ID'] ?? '';
  String get _clientSecret => dotenv.env['SPOTIFY_CLIENT_SECRET'] ?? '';
  String get _redirectUri => dotenv.env['SPOTIFY_REDIRECT_URI'] ?? 'motionsynth://callback';

  /// Returns true if a valid (non-expired) token is stored.
  Future<bool> isAuthenticated() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(_tokenKey);
    final expiry = prefs.getInt(_tokenExpiryKey) ?? 0;
    if (token == null || token.isEmpty) return false;
    return DateTime.now().millisecondsSinceEpoch < expiry;
  }

  /// Launches the Spotify OAuth2 authorization flow in a Chrome Custom Tab.
  Future<bool> authenticate() async {
    final authUrl = Uri.https('accounts.spotify.com', '/authorize', {
      'client_id': _clientId,
      'response_type': 'code',
      'redirect_uri': _redirectUri,
      'scope': 'user-read-private user-read-email',
    });

    try {
      final result = await FlutterWebAuth2.authenticate(
        url: authUrl.toString(),
        callbackUrlScheme: 'motionsynth',
      );

      final code = Uri.parse(result).queryParameters['code'];
      if (code == null) return false;

      return await _exchangeCodeForToken(code);
    } catch (_) {
      return false;
    }
  }

  Future<bool> _exchangeCodeForToken(String code) async {
    final credentials = base64Encode(utf8.encode('$_clientId:$_clientSecret'));

    final response = await http.post(
      Uri.https('accounts.spotify.com', '/api/token'),
      headers: {
        'Authorization': 'Basic $credentials',
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': _redirectUri,
      },
    );

    if (response.statusCode != 200) return false;

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final token = data['access_token'] as String?;
    final expiresIn = data['expires_in'] as int? ?? 3600;

    if (token == null) return false;

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
    await prefs.setInt(
      _tokenExpiryKey,
      DateTime.now().millisecondsSinceEpoch + expiresIn * 1000,
    );

    return true;
  }

  Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  /// Searches Spotify for tracks matching the given genre/mood query.
  Future<List<SpotifyTrack>> searchTracks(String query, {int limit = 20}) async {
    final token = await _getToken();
    if (token == null) return [];

    final response = await http.get(
      Uri.https('api.spotify.com', '/v1/search', {
        'q': query,
        'type': 'track',
        'limit': limit.toString(),
        'market': 'DE',
      }),
      headers: {'Authorization': 'Bearer $token'},
    );

    if (response.statusCode != 200) return [];

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final items = (data['tracks']?['items'] as List<dynamic>?) ?? [];

    return items
        .whereType<Map<String, dynamic>>()
        .map((item) => SpotifyTrack.fromJson(item))
        .toList();
  }

  /// Opens the given Spotify track URI in the Spotify app.
  Future<void> openTrack(SpotifyTrack track) async {
    final spotifyUri = Uri.parse(track.uri);

    if (await canLaunchUrl(spotifyUri)) {
      await launchUrl(spotifyUri, mode: LaunchMode.externalApplication);
    } else {
      // Fallback: open web player
      final webUrl = Uri.parse('https://open.spotify.com/track/${track.id}');
      await launchUrl(webUrl, mode: LaunchMode.externalApplication);
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_tokenExpiryKey);
  }

  /// Returns the current user's display name for the UI header.
  Future<String?> getUserDisplayName() async {
    final token = await _getToken();
    if (token == null) return null;

    final response = await http.get(
      Uri.https('api.spotify.com', '/v1/me'),
      headers: {'Authorization': 'Bearer $token'},
    );

    if (response.statusCode != 200) return null;

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return data['display_name'] as String?;
  }
}
