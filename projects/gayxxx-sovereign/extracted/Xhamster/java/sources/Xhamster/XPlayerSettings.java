package Xhamster;

/* JADX INFO: compiled from: Xhamster.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u00002\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\r\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0000\n\u0002\u0010\u000e\n\u0000\b\u0086\b\u0018\u00002\u00020\u0001B+\u0012\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u0003\u0012\n\b\u0002\u0010\u0004\u001a\u0004\u0018\u00010\u0005\u0012\n\b\u0002\u0010\u0006\u001a\u0004\u0018\u00010\u0007¢\u0006\u0004\b\b\u0010\tJ\u000b\u0010\u0010\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u000b\u0010\u0011\u001a\u0004\u0018\u00010\u0005HÆ\u0003J\u000b\u0010\u0012\u001a\u0004\u0018\u00010\u0007HÆ\u0003J-\u0010\u0013\u001a\u00020\u00002\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u00032\n\b\u0002\u0010\u0004\u001a\u0004\u0018\u00010\u00052\n\b\u0002\u0010\u0006\u001a\u0004\u0018\u00010\u0007HÆ\u0001J\u0014\u0010\u0014\u001a\u00020\u00152\b\u0010\u0016\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\u0017\u001a\u00020\u0018HÖ\u0081\u0004J\n\u0010\u0019\u001a\u00020\u001aHÖ\u0081\u0004R\u0013\u0010\u0002\u001a\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\n\u0010\u000bR\u0013\u0010\u0004\u001a\u0004\u0018\u00010\u0005¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\rR\u0013\u0010\u0006\u001a\u0004\u0018\u00010\u0007¢\u0006\b\n\u0000\u001a\u0004\b\u000e\u0010\u000f¨\u0006\u001b"}, d2 = {"LXhamster/XPlayerSettings;", "", "sources", "LXhamster/VideoSources;", "poster", "LXhamster/Poster;", "subtitles", "LXhamster/Subtitles;", "<init>", "(LXhamster/VideoSources;LXhamster/Poster;LXhamster/Subtitles;)V", "getSources", "()LXhamster/VideoSources;", "getPoster", "()LXhamster/Poster;", "getSubtitles", "()LXhamster/Subtitles;", "component1", "component2", "component3", "copy", "equals", "", "other", "hashCode", "", "toString", "", "Xhamster"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class XPlayerSettings {

    @org.jetbrains.annotations.Nullable
    private final Xhamster.Poster poster;

    @org.jetbrains.annotations.Nullable
    private final Xhamster.VideoSources sources;

    @org.jetbrains.annotations.Nullable
    private final Xhamster.Subtitles subtitles;

    public XPlayerSettings() {
        this(null, null, null, 7, null);
    }

    public static /* synthetic */ Xhamster.XPlayerSettings copy$default(Xhamster.XPlayerSettings xPlayerSettings, Xhamster.VideoSources videoSources, Xhamster.Poster poster, Xhamster.Subtitles subtitles, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            videoSources = xPlayerSettings.sources;
        }
        if ((i & 2) != 0) {
            poster = xPlayerSettings.poster;
        }
        if ((i & 4) != 0) {
            subtitles = xPlayerSettings.subtitles;
        }
        return xPlayerSettings.copy(videoSources, poster, subtitles);
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component1, reason: from getter */
    public final Xhamster.VideoSources getSources() {
        return this.sources;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component2, reason: from getter */
    public final Xhamster.Poster getPoster() {
        return this.poster;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component3, reason: from getter */
    public final Xhamster.Subtitles getSubtitles() {
        return this.subtitles;
    }

    @org.jetbrains.annotations.NotNull
    public final Xhamster.XPlayerSettings copy(@org.jetbrains.annotations.Nullable Xhamster.VideoSources sources, @org.jetbrains.annotations.Nullable Xhamster.Poster poster, @org.jetbrains.annotations.Nullable Xhamster.Subtitles subtitles) {
        return new Xhamster.XPlayerSettings(sources, poster, subtitles);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof Xhamster.XPlayerSettings)) {
            return false;
        }
        Xhamster.XPlayerSettings xPlayerSettings = (Xhamster.XPlayerSettings) other;
        return kotlin.jvm.internal.Intrinsics.areEqual(this.sources, xPlayerSettings.sources) && kotlin.jvm.internal.Intrinsics.areEqual(this.poster, xPlayerSettings.poster) && kotlin.jvm.internal.Intrinsics.areEqual(this.subtitles, xPlayerSettings.subtitles);
    }

    public int hashCode() {
        return ((((this.sources == null ? 0 : this.sources.hashCode()) * 31) + (this.poster == null ? 0 : this.poster.hashCode())) * 31) + (this.subtitles != null ? this.subtitles.hashCode() : 0);
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "XPlayerSettings(sources=" + this.sources + ", poster=" + this.poster + ", subtitles=" + this.subtitles + ')';
    }

    public XPlayerSettings(@org.jetbrains.annotations.Nullable Xhamster.VideoSources sources, @org.jetbrains.annotations.Nullable Xhamster.Poster poster, @org.jetbrains.annotations.Nullable Xhamster.Subtitles subtitles) {
        this.sources = sources;
        this.poster = poster;
        this.subtitles = subtitles;
    }

    public /* synthetic */ XPlayerSettings(Xhamster.VideoSources videoSources, Xhamster.Poster poster, Xhamster.Subtitles subtitles, int i, kotlin.jvm.internal.DefaultConstructorMarker defaultConstructorMarker) {
        this((i & 1) != 0 ? null : videoSources, (i & 2) != 0 ? null : poster, (i & 4) != 0 ? null : subtitles);
    }

    @org.jetbrains.annotations.Nullable
    public final Xhamster.VideoSources getSources() {
        return this.sources;
    }

    @org.jetbrains.annotations.Nullable
    public final Xhamster.Poster getPoster() {
        return this.poster;
    }

    @org.jetbrains.annotations.Nullable
    public final Xhamster.Subtitles getSubtitles() {
        return this.subtitles;
    }
}
