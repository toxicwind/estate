package Xhamster;

/* JADX INFO: compiled from: Xhamster.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000,\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\n\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0000\n\u0002\u0010\u000e\n\u0000\b\u0086\b\u0018\u00002\u00020\u0001B\u001f\u0012\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u0003\u0012\n\b\u0002\u0010\u0004\u001a\u0004\u0018\u00010\u0005¢\u0006\u0004\b\u0006\u0010\u0007J\u000b\u0010\f\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u000b\u0010\r\u001a\u0004\u0018\u00010\u0005HÆ\u0003J!\u0010\u000e\u001a\u00020\u00002\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u00032\n\b\u0002\u0010\u0004\u001a\u0004\u0018\u00010\u0005HÆ\u0001J\u0014\u0010\u000f\u001a\u00020\u00102\b\u0010\u0011\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\u0012\u001a\u00020\u0013HÖ\u0081\u0004J\n\u0010\u0014\u001a\u00020\u0015HÖ\u0081\u0004R\u0013\u0010\u0002\u001a\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\b\u0010\tR\u0013\u0010\u0004\u001a\u0004\u0018\u00010\u0005¢\u0006\b\n\u0000\u001a\u0004\b\n\u0010\u000b¨\u0006\u0016"}, d2 = {"LXhamster/VideoSources;", "", "hls", "LXhamster/HlsSources;", "standard", "LXhamster/StandardSources;", "<init>", "(LXhamster/HlsSources;LXhamster/StandardSources;)V", "getHls", "()LXhamster/HlsSources;", "getStandard", "()LXhamster/StandardSources;", "component1", "component2", "copy", "equals", "", "other", "hashCode", "", "toString", "", "Xhamster"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class VideoSources {

    @org.jetbrains.annotations.Nullable
    private final Xhamster.HlsSources hls;

    @org.jetbrains.annotations.Nullable
    private final Xhamster.StandardSources standard;

    /* JADX WARN: Multi-variable type inference failed */
    public VideoSources() {
        this(null, 0 == true ? 1 : 0, 3, 0 == true ? 1 : 0);
    }

    public static /* synthetic */ Xhamster.VideoSources copy$default(Xhamster.VideoSources videoSources, Xhamster.HlsSources hlsSources, Xhamster.StandardSources standardSources, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            hlsSources = videoSources.hls;
        }
        if ((i & 2) != 0) {
            standardSources = videoSources.standard;
        }
        return videoSources.copy(hlsSources, standardSources);
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component1, reason: from getter */
    public final Xhamster.HlsSources getHls() {
        return this.hls;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component2, reason: from getter */
    public final Xhamster.StandardSources getStandard() {
        return this.standard;
    }

    @org.jetbrains.annotations.NotNull
    public final Xhamster.VideoSources copy(@org.jetbrains.annotations.Nullable Xhamster.HlsSources hls, @org.jetbrains.annotations.Nullable Xhamster.StandardSources standard) {
        return new Xhamster.VideoSources(hls, standard);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof Xhamster.VideoSources)) {
            return false;
        }
        Xhamster.VideoSources videoSources = (Xhamster.VideoSources) other;
        return kotlin.jvm.internal.Intrinsics.areEqual(this.hls, videoSources.hls) && kotlin.jvm.internal.Intrinsics.areEqual(this.standard, videoSources.standard);
    }

    public int hashCode() {
        return ((this.hls == null ? 0 : this.hls.hashCode()) * 31) + (this.standard != null ? this.standard.hashCode() : 0);
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "VideoSources(hls=" + this.hls + ", standard=" + this.standard + ')';
    }

    public VideoSources(@org.jetbrains.annotations.Nullable Xhamster.HlsSources hls, @org.jetbrains.annotations.Nullable Xhamster.StandardSources standard) {
        this.hls = hls;
        this.standard = standard;
    }

    public /* synthetic */ VideoSources(Xhamster.HlsSources hlsSources, Xhamster.StandardSources standardSources, int i, kotlin.jvm.internal.DefaultConstructorMarker defaultConstructorMarker) {
        this((i & 1) != 0 ? null : hlsSources, (i & 2) != 0 ? null : standardSources);
    }

    @org.jetbrains.annotations.Nullable
    public final Xhamster.HlsSources getHls() {
        return this.hls;
    }

    @org.jetbrains.annotations.Nullable
    public final Xhamster.StandardSources getStandard() {
        return this.standard;
    }
}
