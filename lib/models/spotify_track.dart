class SpotifyTrack {
  final String id;
  final String name;
  final String artist;
  final String? albumArtUrl;
  final String uri;
  final String? previewUrl;

  const SpotifyTrack({
    required this.id,
    required this.name,
    required this.artist,
    this.albumArtUrl,
    required this.uri,
    this.previewUrl,
  });

  factory SpotifyTrack.fromJson(Map<String, dynamic> json) {
    final artists = json['artists'] as List<dynamic>;
    final artistNames = artists.map((a) => a['name'] as String).join(', ');

    final album = json['album'] as Map<String, dynamic>?;
    final images = album?['images'] as List<dynamic>?;
    final artUrl = images != null && images.isNotEmpty
        ? images[0]['url'] as String?
        : null;

    return SpotifyTrack(
      id: json['id'] as String,
      name: json['name'] as String,
      artist: artistNames,
      albumArtUrl: artUrl,
      uri: json['uri'] as String,
      previewUrl: json['preview_url'] as String?,
    );
  }
}
