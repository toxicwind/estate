package Xhamster;

/* JADX INFO: compiled from: Xhamster.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000*\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010\u000e\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\b\f\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0002\b\u0002\b\u0086\b\u0018\u00002\u00020\u0001B+\u0012\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u0003\u0012\n\b\u0002\u0010\u0004\u001a\u0004\u0018\u00010\u0003\u0012\n\b\u0002\u0010\u0005\u001a\u0004\u0018\u00010\u0006¢\u0006\u0004\b\u0007\u0010\bJ\u000b\u0010\u000e\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u000b\u0010\u000f\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u000b\u0010\u0010\u001a\u0004\u0018\u00010\u0006HÆ\u0003J-\u0010\u0011\u001a\u00020\u00002\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u00032\n\b\u0002\u0010\u0004\u001a\u0004\u0018\u00010\u00032\n\b\u0002\u0010\u0005\u001a\u0004\u0018\u00010\u0006HÆ\u0001J\u0014\u0010\u0012\u001a\u00020\u00132\b\u0010\u0014\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\u0015\u001a\u00020\u0016HÖ\u0081\u0004J\n\u0010\u0017\u001a\u00020\u0003HÖ\u0081\u0004R\u0013\u0010\u0002\u001a\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\nR\u0013\u0010\u0004\u001a\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u000b\u0010\nR\u0013\u0010\u0005\u001a\u0004\u0018\u00010\u0006¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\r¨\u0006\u0018"}, d2 = {"LXhamster/SubtitleTrack;", "", "label", "", "lang", "urls", "LXhamster/SubtitleUrls;", "<init>", "(Ljava/lang/String;Ljava/lang/String;LXhamster/SubtitleUrls;)V", "getLabel", "()Ljava/lang/String;", "getLang", "getUrls", "()LXhamster/SubtitleUrls;", "component1", "component2", "component3", "copy", "equals", "", "other", "hashCode", "", "toString", "Xhamster"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class SubtitleTrack {

    @org.jetbrains.annotations.Nullable
    private final java.lang.String label;

    @org.jetbrains.annotations.Nullable
    private final java.lang.String lang;

    @org.jetbrains.annotations.Nullable
    private final Xhamster.SubtitleUrls urls;

    public SubtitleTrack() {
        this(null, null, null, 7, null);
    }

    public static /* synthetic */ Xhamster.SubtitleTrack copy$default(Xhamster.SubtitleTrack subtitleTrack, java.lang.String str, java.lang.String str2, Xhamster.SubtitleUrls subtitleUrls, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            str = subtitleTrack.label;
        }
        if ((i & 2) != 0) {
            str2 = subtitleTrack.lang;
        }
        if ((i & 4) != 0) {
            subtitleUrls = subtitleTrack.urls;
        }
        return subtitleTrack.copy(str, str2, subtitleUrls);
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component1, reason: from getter */
    public final java.lang.String getLabel() {
        return this.label;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component2, reason: from getter */
    public final java.lang.String getLang() {
        return this.lang;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component3, reason: from getter */
    public final Xhamster.SubtitleUrls getUrls() {
        return this.urls;
    }

    @org.jetbrains.annotations.NotNull
    public final Xhamster.SubtitleTrack copy(@org.jetbrains.annotations.Nullable java.lang.String label, @org.jetbrains.annotations.Nullable java.lang.String lang, @org.jetbrains.annotations.Nullable Xhamster.SubtitleUrls urls) {
        return new Xhamster.SubtitleTrack(label, lang, urls);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof Xhamster.SubtitleTrack)) {
            return false;
        }
        Xhamster.SubtitleTrack subtitleTrack = (Xhamster.SubtitleTrack) other;
        return kotlin.jvm.internal.Intrinsics.areEqual(this.label, subtitleTrack.label) && kotlin.jvm.internal.Intrinsics.areEqual(this.lang, subtitleTrack.lang) && kotlin.jvm.internal.Intrinsics.areEqual(this.urls, subtitleTrack.urls);
    }

    public int hashCode() {
        return ((((this.label == null ? 0 : this.label.hashCode()) * 31) + (this.lang == null ? 0 : this.lang.hashCode())) * 31) + (this.urls != null ? this.urls.hashCode() : 0);
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "SubtitleTrack(label=" + this.label + ", lang=" + this.lang + ", urls=" + this.urls + ')';
    }

    public SubtitleTrack(@org.jetbrains.annotations.Nullable java.lang.String label, @org.jetbrains.annotations.Nullable java.lang.String lang, @org.jetbrains.annotations.Nullable Xhamster.SubtitleUrls urls) {
        this.label = label;
        this.lang = lang;
        this.urls = urls;
    }

    public /* synthetic */ SubtitleTrack(java.lang.String str, java.lang.String str2, Xhamster.SubtitleUrls subtitleUrls, int i, kotlin.jvm.internal.DefaultConstructorMarker defaultConstructorMarker) {
        this((i & 1) != 0 ? null : str, (i & 2) != 0 ? null : str2, (i & 4) != 0 ? null : subtitleUrls);
    }

    @org.jetbrains.annotations.Nullable
    public final java.lang.String getLabel() {
        return this.label;
    }

    @org.jetbrains.annotations.Nullable
    public final java.lang.String getLang() {
        return this.lang;
    }

    @org.jetbrains.annotations.Nullable
    public final Xhamster.SubtitleUrls getUrls() {
        return this.urls;
    }
}
