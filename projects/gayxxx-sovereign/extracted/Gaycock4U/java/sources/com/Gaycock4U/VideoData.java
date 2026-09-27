package com.Gaycock4U;

/* JADX INFO: compiled from: Extractor.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000.\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010\u000e\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u000e\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0002\b\u0002\b\u0086\b\u0018\u00002\u00020\u0001B5\u0012\b\u0010\u0002\u001a\u0004\u0018\u00010\u0003\u0012\b\u0010\u0004\u001a\u0004\u0018\u00010\u0003\u0012\b\u0010\u0005\u001a\u0004\u0018\u00010\u0003\u0012\u000e\u0010\u0006\u001a\n\u0012\u0004\u0012\u00020\b\u0018\u00010\u0007¢\u0006\u0004\b\t\u0010\nJ\u000b\u0010\u0011\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u000b\u0010\u0012\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u000b\u0010\u0013\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u0011\u0010\u0014\u001a\n\u0012\u0004\u0012\u00020\b\u0018\u00010\u0007HÆ\u0003J?\u0010\u0015\u001a\u00020\u00002\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u00032\n\b\u0002\u0010\u0004\u001a\u0004\u0018\u00010\u00032\n\b\u0002\u0010\u0005\u001a\u0004\u0018\u00010\u00032\u0010\b\u0002\u0010\u0006\u001a\n\u0012\u0004\u0012\u00020\b\u0018\u00010\u0007HÆ\u0001J\u0014\u0010\u0016\u001a\u00020\u00172\b\u0010\u0018\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\u0019\u001a\u00020\u001aHÖ\u0081\u0004J\n\u0010\u001b\u001a\u00020\u0003HÖ\u0081\u0004R\u0013\u0010\u0002\u001a\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u000b\u0010\fR\u0013\u0010\u0004\u001a\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\r\u0010\fR\u0013\u0010\u0005\u001a\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u000e\u0010\fR\u0019\u0010\u0006\u001a\n\u0012\u0004\u0012\u00020\b\u0018\u00010\u0007¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010¨\u0006\u001c"}, d2 = {"Lcom/Gaycock4U/VideoData;", "", "id", "", "title", "poster", "sources", "", "Lcom/Gaycock4U/VideoSource;", "<init>", "(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/util/List;)V", "getId", "()Ljava/lang/String;", "getTitle", "getPoster", "getSources", "()Ljava/util/List;", "component1", "component2", "component3", "component4", "copy", "equals", "", "other", "hashCode", "", "toString", "Gaycock4U"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class VideoData {

    @org.jetbrains.annotations.Nullable
    private final java.lang.String id;

    @org.jetbrains.annotations.Nullable
    private final java.lang.String poster;

    @org.jetbrains.annotations.Nullable
    private final java.util.List<com.Gaycock4U.VideoSource> sources;

    @org.jetbrains.annotations.Nullable
    private final java.lang.String title;

    /* JADX WARN: Multi-variable type inference failed */
    public static /* synthetic */ com.Gaycock4U.VideoData copy$default(com.Gaycock4U.VideoData videoData, java.lang.String str, java.lang.String str2, java.lang.String str3, java.util.List list, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            str = videoData.id;
        }
        if ((i & 2) != 0) {
            str2 = videoData.title;
        }
        if ((i & 4) != 0) {
            str3 = videoData.poster;
        }
        if ((i & 8) != 0) {
            list = videoData.sources;
        }
        return videoData.copy(str, str2, str3, list);
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component1, reason: from getter */
    public final java.lang.String getId() {
        return this.id;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component2, reason: from getter */
    public final java.lang.String getTitle() {
        return this.title;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component3, reason: from getter */
    public final java.lang.String getPoster() {
        return this.poster;
    }

    @org.jetbrains.annotations.Nullable
    public final java.util.List<com.Gaycock4U.VideoSource> component4() {
        return this.sources;
    }

    @org.jetbrains.annotations.NotNull
    public final com.Gaycock4U.VideoData copy(@org.jetbrains.annotations.Nullable java.lang.String id, @org.jetbrains.annotations.Nullable java.lang.String title, @org.jetbrains.annotations.Nullable java.lang.String poster, @org.jetbrains.annotations.Nullable java.util.List<com.Gaycock4U.VideoSource> sources) {
        return new com.Gaycock4U.VideoData(id, title, poster, sources);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof com.Gaycock4U.VideoData)) {
            return false;
        }
        com.Gaycock4U.VideoData videoData = (com.Gaycock4U.VideoData) other;
        return kotlin.jvm.internal.Intrinsics.areEqual(this.id, videoData.id) && kotlin.jvm.internal.Intrinsics.areEqual(this.title, videoData.title) && kotlin.jvm.internal.Intrinsics.areEqual(this.poster, videoData.poster) && kotlin.jvm.internal.Intrinsics.areEqual(this.sources, videoData.sources);
    }

    public int hashCode() {
        return ((((((this.id == null ? 0 : this.id.hashCode()) * 31) + (this.title == null ? 0 : this.title.hashCode())) * 31) + (this.poster == null ? 0 : this.poster.hashCode())) * 31) + (this.sources != null ? this.sources.hashCode() : 0);
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "VideoData(id=" + this.id + ", title=" + this.title + ", poster=" + this.poster + ", sources=" + this.sources + ')';
    }

    public VideoData(@org.jetbrains.annotations.Nullable java.lang.String id, @org.jetbrains.annotations.Nullable java.lang.String title, @org.jetbrains.annotations.Nullable java.lang.String poster, @org.jetbrains.annotations.Nullable java.util.List<com.Gaycock4U.VideoSource> list) {
        this.id = id;
        this.title = title;
        this.poster = poster;
        this.sources = list;
    }

    @org.jetbrains.annotations.Nullable
    public final java.lang.String getId() {
        return this.id;
    }

    @org.jetbrains.annotations.Nullable
    public final java.lang.String getPoster() {
        return this.poster;
    }

    @org.jetbrains.annotations.Nullable
    public final java.util.List<com.Gaycock4U.VideoSource> getSources() {
        return this.sources;
    }

    @org.jetbrains.annotations.Nullable
    public final java.lang.String getTitle() {
        return this.title;
    }
}
